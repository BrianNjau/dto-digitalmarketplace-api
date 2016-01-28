from flask import jsonify, abort, current_app, request

from dmapiclient.audit import AuditTypes
from .. import main
from ... import db
from ...utils import get_json_from_request, json_has_required_keys, pagination_links, get_valid_page_or_1
from ...service_utils import validate_and_return_lot, validate_and_return_updater_request
from ...models import User, Brief, AuditEvent
from ...brief_utils import validate_brief_data


@main.route('/briefs', methods=['POST'])
def create_brief():
    updater_json = validate_and_return_updater_request()
    json_payload = get_json_from_request()
    json_has_required_keys(json_payload, ['briefs'])
    brief_json = json_payload['briefs']

    json_has_required_keys(brief_json, ['frameworkSlug', 'lot', 'userId'])

    framework, lot = validate_and_return_lot(brief_json)

    user = User.query.get(brief_json.pop('userId'))

    if user is None:
        abort(400, "User ID does not exist")

    brief = Brief(data=brief_json, users=[user], framework=framework, lot=lot)
    validate_brief_data(brief)

    db.session.add(brief)
    try:
        db.session.flush()
    except IntegrityError as e:
        db.session.rollback()
        abort(400, e.orig)

    audit = AuditEvent(
        audit_type=AuditTypes.create_brief,
        user=updater_json['updated_by'],
        data={
            'briefId': brief.id,
            'briefJson': brief_json,
        },
        db_object=brief,
    )

    db.session.add(audit)

    db.session.commit()

    return jsonify(briefs=brief.serialize()), 201


@main.route('/briefs/<int:brief_id>', methods=['POST'])
def update_brief(brief_id):
    updater_json = validate_and_return_updater_request()
    json_payload = get_json_from_request()
    json_has_required_keys(json_payload, ['briefs'])
    brief_json = json_payload['briefs']

    brief = Brief.query.filter(
        Brief.id == brief_id
    ).first_or_404()

    brief.update_from_json(brief_json)
    validate_brief_data(brief)

    audit = AuditEvent(
        audit_type=AuditTypes.update_brief,
        user=updater_json['updated_by'],
        data={
            'briefId': brief.id,
            'briefJson': brief_json,
        },
        db_object=brief,
    )

    db.session.add(brief)
    db.session.add(audit)
    db.session.commit()

    return jsonify(briefs=brief.serialize()), 200


@main.route('/briefs/<int:brief_id>', methods=['GET'])
def get_brief(brief_id):
    brief = Brief.query.filter(
        Brief.id == brief_id
    ).first_or_404()

    return jsonify(briefs=brief.serialize())


@main.route('/briefs', methods=['GET'])
def list_briefs():
    page = get_valid_page_or_1()

    briefs = Brief.query.order_by(Brief.id)
    briefs = briefs.paginate(
        page=page,
        per_page=current_app.config['DM_API_BRIEFS_PAGE_SIZE'])

    return jsonify(
        briefs=[brief.serialize() for brief in briefs.items],
        links=pagination_links(
            briefs,
            '.list_briefs',
            request.args
        )
    )
