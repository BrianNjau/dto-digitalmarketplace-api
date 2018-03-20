from operator import itemgetter

from dmapiclient.audit import AuditTypes

from flask import jsonify, abort, request, current_app

from .. import main
from ...models import ArchivedService, Service, ServiceRole, Supplier, AuditEvent, Framework, ValidationError,\
    PriceSchedule, ServiceType, db, Region, Location, ServiceTypePrice, ServiceTypePriceCeiling, ServiceSubType

from sqlalchemy import asc
from ...validation import is_valid_service_id_or_400
from ...utils import (
    url_for, pagination_links, display_list, get_valid_page_or_1,
    validate_and_return_updater_request, get_int_or_400
)
from pendulum import Pendulum
from ...service_utils import (
    validate_and_return_service_request,
    update_and_validate_service,
    index_service,
    delete_service_from_index,
    commit_and_archive_service,
    validate_service_data,
    validate_and_return_related_objects,
    filter_services)

from app.utils import (get_json_from_request, json_has_required_keys)


@main.route('/')
def index():
    """Entry point for the API, show the resources that are available."""
    return jsonify(links={
        "audits.list": url_for('.list_audits', _external=True),
        "services.list": url_for('.list_services', _external=True),
        "suppliers.list": url_for('.list_suppliers', _external=True),
        "frameworks.list": url_for('.list_frameworks', _external=True),
    }
    ), 200


@main.route('/roles', methods=['GET'])
def list_service_roles():
    roles = ServiceRole.query.all()

    def serialize_with_abbreviations(role):
        return {
            'category': role.category.name,
            'categoryAbbreviation': role.category.abbreviation,
            'role': role.name,
            'roleAbbreviation': role.abbreviation,
        }

    return jsonify(roles=[serialize_with_abbreviations(r) for r in roles])


@main.route('/roles/count', methods=['GET'])
def get_roles_stats():
    top_roles = []
    all_roles = ServiceRole.query.all()

    for role in all_roles:
        name = role.name.replace('Junior', '').replace('Senior', '').strip()
        count = PriceSchedule.query.filter(PriceSchedule.service_role_id == role.id).count()
        dict_exist = False
        for top_role in top_roles:
            if top_role['name'] == name:
                top_role['count'] += count
                dict_exist = True

        if not dict_exist:
            role_data = {
                'name': name,
                'count': count
            }
            top_roles.append(role_data)

    roles = {
        'top_roles': sorted(top_roles, key=itemgetter('count'), reverse=True)
    }

    return jsonify(roles=roles)


@main.route('/services', methods=['GET'])
def list_services():
    page = get_valid_page_or_1()

    supplier_code = get_int_or_400(request.args, 'supplier_code')

    if request.args.get('framework'):
        frameworks = [slug.strip() for slug in request.args['framework'].split(',')]
    else:
        frameworks = None

    if request.args.get('status'):
        statuses = [status.strip() for status in request.args['status'].split(',')]
    else:
        statuses = None

    try:
        services = filter_services(
            framework_slugs=frameworks,
            statuses=statuses,
            lot_slug=request.args.get('lot'),
            location=request.args.get('location'),
            role=request.args.get('role')
        )
    except ValidationError as e:
        abort(400, e.message)

    if supplier_code is not None:
        supplier = Supplier.query.filter(Supplier.code == supplier_code).all()
        if not supplier:
            abort(404, "supplier_code '%d' not found" % supplier_code)

        items = services.default_order().filter(Service.supplier_code == supplier_code).all()
        return jsonify(
            services=[service.serialize() for service in items],
            links=dict()
        )
    else:
        services = services.order_by(asc(Service.id))

    services = services.paginate(
        page=page,
        per_page=current_app.config['DM_API_SERVICES_PAGE_SIZE'],
    )

    return jsonify(
        services=[service.serialize() for service in services.items],
        links=pagination_links(
            services,
            '.list_services',
            request.args
        )
    )


@main.route('/archived-services', methods=['GET'])
def list_archived_services_by_service_id():
    """
    Retrieves a list of services from the archived_services table
    for the supplied service_id
    :query_param service_id:
    :return: List[service]
    """

    is_valid_service_id_or_400(request.args.get("service-id", "no service id"))
    service_id = request.args.get("service-id", "no service id")

    page = get_valid_page_or_1()

    services = ArchivedService.query.filter(
        ArchivedService.service_id == service_id
    ).order_by(asc(ArchivedService.id))

    services = services.paginate(
        page=page,
        per_page=current_app.config['DM_API_SERVICES_PAGE_SIZE'],
    )

    if request.args and not services.items:
        abort(404)
    return jsonify(
        services=[service.serialize() for service in services.items],
        links=pagination_links(
            services,
            '.list_services',
            request.args
        )
    )


@main.route('/services/<string:service_id>', methods=['POST'])
def update_service(service_id):
    """
        Update a service. Looks service up in DB, and updates the JSON listing.
    """

    is_valid_service_id_or_400(service_id)

    service = Service.query.filter(
        Service.service_id == service_id
    ).first_or_404()

    update_details = validate_and_return_updater_request()
    update = validate_and_return_service_request(service_id)

    updated_service = update_and_validate_service(service, update)

    commit_and_archive_service(updated_service, update_details,
                               AuditTypes.update_service)
    index_service(updated_service)

    return jsonify(message="done"), 200


@main.route('/services/<string:service_id>', methods=['PUT'])
def import_service(service_id):
    """Import services from legacy digital marketplace

    This endpoint creates new services where we have an existing ID, it
    should not be used as a model for how we add new services.
    """
    is_valid_service_id_or_400(service_id)

    service = Service.query.filter(
        Service.service_id == service_id
    ).first()

    if service is not None:
        abort(400, "Cannot update service by PUT")

    updater_json = validate_and_return_updater_request()
    service_data = validate_and_return_service_request(service_id)

    framework, lot, supplier = validate_and_return_related_objects(service_data)

    service = Service(
        service_id=service_id,
        supplier=supplier,
        lot=lot,
        framework=framework,
        status=service_data.get('status', 'published'),
        created_at=service_data.get('createdAt'),
        updated_at=service_data.get('updatedAt'),
        data=service_data,
    )

    validate_service_data(service)

    commit_and_archive_service(service, updater_json, AuditTypes.import_service)
    index_service(service)

    return jsonify(services=service.serialize()), 201


@main.route('/services/<string:service_id>', methods=['GET'])
def get_service(service_id):
    service = Service.query.filter(
        Service.service_id == service_id
    ).first_or_404()

    service_made_unavailable_audit_event = None
    service_is_unavailable = False
    if service.framework.status == 'expired':
        service_is_unavailable = True
        audit_event_object_reference = Framework.query.filter(
            Framework.id == service.framework.id
        ).first_or_404()
        audit_event_update_type = AuditTypes.framework_update.value
    elif service.status != 'published':
        service_is_unavailable = True
        audit_event_object_reference = service
        audit_event_update_type = AuditTypes.update_service_status.value

    if service_is_unavailable:
        service_made_unavailable_audit_event = AuditEvent.query.last_for_object(
            audit_event_object_reference, [audit_event_update_type]
        )

    if service_made_unavailable_audit_event is not None:
        service_made_unavailable_audit_event = service_made_unavailable_audit_event.serialize()

    return jsonify(
        services=service.serialize(),
        serviceMadeUnavailableAuditEvent=service_made_unavailable_audit_event
    )


@main.route('/archived-services/<int:archived_service_id>', methods=['GET'])
def get_archived_service(archived_service_id):
    """
    Retrieves a service from the archived_service by PK
    :param archived_service_id:
    :return: service
    """

    service = ArchivedService.query.filter(
        ArchivedService.id == archived_service_id
    ).first_or_404()

    return jsonify(services=service.serialize())


@main.route(
    '/services/<string:service_id>/status/<string:status>',
    methods=['POST']
)
def update_service_status(service_id, status):
    """
    Updates the status parameter of a service, and archives the old one.
    :param service_id:
    :param status:
    :return: the newly updated service in the response
    """

    # Statuses are defined in the Supplier model
    valid_statuses = [
        "published",
        "enabled",
        "disabled"
    ]

    is_valid_service_id_or_400(service_id)

    service = Service.query.filter(
        Service.service_id == service_id
    ).first_or_404()

    if status not in valid_statuses:
        valid_statuses_single_quotes = display_list(
            ["\'{}\'".format(vstatus) for vstatus in valid_statuses]
        )
        abort(400, "'{}' is not a valid status. Valid statuses are {}".format(
            status, valid_statuses_single_quotes
        ))

    update_json = validate_and_return_updater_request()

    prior_status, service.status = service.status, status

    commit_and_archive_service(service, update_json,
                               AuditTypes.update_service_status,
                               audit_data={'old_status': prior_status,
                                           'new_status': status})

    if prior_status != status:

        # If it's being unpublished, delete it from the search api.
        if prior_status == 'published':
            delete_service_from_index(service)
        else:
            # If it's being published, index in the search api.
            index_service(service)

    return jsonify(services=service.serialize()), 200


@main.route('/service-types/<string:service_type_id>', methods=['GET'])
def get_service_type(service_type_id):
    service_type = ServiceType.query.filter(
        ServiceType.id == service_type_id
    ).first_or_404()

    return jsonify(
        service_type=service_type.serializable
    )


@main.route('/service-types', methods=['POST'])
def add_service_type():
    service_type_json = get_json_from_request()
    json_has_required_keys(service_type_json, ['service_type'])

    service_type = ServiceType()
    service_type.update_from_json(service_type_json['service_type'])

    db.session.add(service_type)
    db.session.commit()

    return jsonify(service_type=service_type.serializable), 201


@main.route('/regions', methods=['POST'])
def add_region():
    region_json = get_json_from_request()
    json_has_required_keys(region_json, ['region'])

    region = Region.query.filter(
        Region.name == region_json['region']['name'],
        Region.state == region_json['region']['state']
    ).first()

    if region is not None:
        return jsonify(region=region.serializable), 200

    region = Region()
    region.update_from_json(region_json['region'])

    db.session.add(region)
    db.session.commit()

    return jsonify(region=region.serializable), 201


@main.route('/locations', methods=['POST'])
def add_location():
    location_json = get_json_from_request()
    json_has_required_keys(location_json, ['location'])

    location = Location()
    location.update_from_json(location_json['location'])

    db.session.add(location)
    db.session.commit()

    return jsonify(location=location.serializable), 201


@main.route('/service-type-prices', methods=['POST'])
def add_service_type_price():
    price_json = get_json_from_request()
    json_has_required_keys(price_json, ['price'])

    price = ServiceTypePrice()
    price.update_from_json(price_json['price'])

    today = Pendulum.today()
    tomorrow = Pendulum.tomorrow()
    service_type_prices = (
        ServiceTypePrice.query.filter(ServiceTypePrice.supplier_code == price.supplier_code,
                                      ServiceTypePrice.service_type_id == price.service_type_id,
                                      ServiceTypePrice.sub_service_id == price.sub_service_id,
                                      ServiceTypePrice.region_id == price.region_id)
                              .order_by(ServiceTypePrice.updated_at.desc())
                              .all())

    # look for current price
    current_service_type_price = None
    current_service_type_prices = [c for c in service_type_prices if c.date_from < today and c.date_to >= today]
    current_service_type_prices_length = len(current_service_type_prices)
    if current_service_type_prices_length >= 1:
        # takes the one with the latest update date
        current_service_type_price = current_service_type_prices[0]

    # look for future price
    future_service_type_price = None
    future_service_type_prices = [c for c in service_type_prices if c.date_from <= tomorrow and c.date_to > tomorrow]
    future_service_type_prices_length = len(future_service_type_prices)
    if future_service_type_prices_length >= 1:
        # takes the one with the latest update date
        future_service_type_price = future_service_type_prices[0]

    if current_service_type_price is not None and (future_service_type_price is None or
                                                   future_service_type_price.id == current_service_type_price.id):
        if current_service_type_price.price != price.price:
            # Only add record when there are no future prices
            current_service_type_price.updated_at = Pendulum.utcnow()
            current_service_type_price.date_to = today

            price.date_from = tomorrow
            price.date_to = Pendulum(2050, 1, 1)

            db.session.add(current_service_type_price)
            db.session.add(price)
            db.session.commit()
            return jsonify(price=price.serializable,
                           msg="Expired current price. Added new price"), 201
        else:
            return jsonify(price=current_service_type_price,
                           msg="No changes made. Price is the same."), 200

    if future_service_type_price is not None:
        if future_service_type_price.price != price.price:
            # Update future record. This should only happen when the import is executed mulitple times during the day.
            # Assumming this is okay because the prices is not in effect yet.
            future_service_type_price.price = price.price
            future_service_type_price.updated_at = Pendulum.utcnow()
            db.session.add(future_service_type_price)
            db.session.commit()
            return jsonify(price=future_service_type_price.serializable,
                           msg="Updated future price record."), 201
        else:
            return jsonify(price=future_service_type_price.serializable,
                           msg="No changes made. Price is the same."), 200

    price.date_from = tomorrow
    price.date_to = Pendulum(2050, 1, 1)
    db.session.add(price)
    db.session.commit()
    return jsonify(price=price.serializable, msg="Added price"), 201


@main.route('/service-type-price-ceilings', methods=['POST'])
def add_service_type_price_ceilings():
    price_json = get_json_from_request()
    json_has_required_keys(price_json, ['price'])

    price = ServiceTypePriceCeiling()
    price.update_from_json(price_json['price'])

    service_type_price_ceiling = ServiceTypePriceCeiling.query.filter(
        ServiceTypePriceCeiling.supplier_code == price.supplier_code,
        ServiceTypePriceCeiling.service_type_id == price.service_type_id,
        ServiceTypePriceCeiling.sub_service_id == price.sub_service_id,
        ServiceTypePriceCeiling.region_id == price.region_id
    ).one_or_none()

    if service_type_price_ceiling is not None:
        if service_type_price_ceiling.price != price.price:
            service_type_price_ceiling.price = price.price
            service_type_price_ceiling.updated_at = Pendulum.utcnow()
            db.session.add(service_type_price_ceiling)
            db.session.commit()
            return jsonify(price_ceiling=price.serializable,
                           msg="Updated price ceiling record."), 201
        else:
            return jsonify(price_ceiling=price.serializable,
                           msg="No changes made. Price is the same."), 200

    db.session.add(price)
    db.session.commit()

    return jsonify(price_ceiling=price.serializable,
                   msg="Added price ceiling record."), 201


@main.route('/service-sub-types', methods=['POST'])
def add_service_sub_type():
    service_sub_type_json = get_json_from_request()
    json_has_required_keys(service_sub_type_json, ['service_sub_type'])

    service_sub_type = ServiceSubType()
    service_sub_type.update_from_json(service_sub_type_json['service_sub_type'])

    db.session.add(service_sub_type)
    db.session.commit()

    return jsonify(service_sub_type=service_sub_type.serializable), 201
