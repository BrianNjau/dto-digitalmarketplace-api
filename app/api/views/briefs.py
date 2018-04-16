import os

from flask import jsonify, request, current_app, Response
from flask_login import current_user, login_required
from app.api import api
from app.api.services import (briefs, brief_responses_service,
                              lots_service,
                              audit_service,
                              audit_types,
                              suppliers)
from app.api.helpers import role_required, abort, forbidden, not_found
from app.emails import send_brief_response_received_email, send_seller_email
from ...models import (db, AuditEvent, Brief, BriefResponse,
                       Supplier, Framework, ValidationError)
from sqlalchemy.exc import DataError
from ...utils import (
    get_json_from_request
)
from dmutils.file import s3_upload_file_from_request, s3_download_file
import mimetypes
import rollbar
import json


def _can_do_brief_response(brief_id):
    try:
        brief = Brief.query.get(brief_id)
    except DataError:
        brief = None

    if brief is None:
        abort("Invalid brief ID '{}'".format(brief_id))

    if brief.status != 'live':
        abort("Brief must be live")

    if brief.framework.status != 'live':
        abort("Brief framework must be live")

    if not hasattr(current_user, 'role') or current_user.role != 'supplier':
        forbidden("Only supplier role users can respond to briefs")

    try:
        supplier = Supplier.query.filter(
            Supplier.code == current_user.supplier_code
        ).first()
    except DataError:
        supplier = None

    if not supplier:
        forbidden("Invalid supplier Code '{}'".format(current_user.supplier_code))

    def domain(email):
        return email.split('@')[-1]

    current_user_domain = domain(current_user.email_address) \
        if domain(current_user.email_address) not in current_app.config.get('GENERIC_EMAIL_DOMAINS') \
        else None

    if brief.data.get('sellerSelector', '') == 'someSellers':
        seller_domain_list = [domain(x).lower() for x in brief.data['sellerEmailList']]
        if current_user.email_address not in brief.data['sellerEmailList'] \
                and (not current_user_domain or current_user_domain.lower() not in seller_domain_list):
            forbidden("Supplier not selected for this brief")
    if brief.data.get('sellerSelector', '') == 'oneSeller':
        if current_user.email_address.lower() != brief.data['sellerEmail'].lower() \
                and (not current_user_domain or
                     current_user_domain.lower() != domain(brief.data['sellerEmail'].lower())):
            forbidden("Supplier not selected for this brief")

    if len(supplier.frameworks) == 0 \
            or 'digital-marketplace' != supplier.frameworks[0].framework.slug \
            or len(supplier.assessed_domains) == 0:
        abort("Supplier does not have Digital Marketplace framework "
              "or does not have at least one assessed domain")

    lot = lots_service.first(slug='digital-professionals')
    if brief.lot_id == lot.id:
        # Check if there are more than 3 brief response already from this supplier when professional aka specialists
        brief_response_count = brief_responses_service.find(supplier_code=supplier.code,
                                                            brief_id=brief.id,
                                                            withdrawn_at=None).count()
        if (brief_response_count > 2):  # TODO magic number
            abort("There are already 3 brief responses for supplier '{}'".format(supplier.code))
    else:
        # Check if brief response already exists from this supplier when outcome for all other types
        if brief_responses_service.find(supplier_code=supplier.code,
                                        brief_id=brief.id,
                                        withdrawn_at=None).one_or_none():
            abort("Brief response already exists for supplier '{}'".format(supplier.code))

    return supplier, brief


@api.route('/brief/<int:brief_id>', methods=["GET"])
def get_brief(brief_id):
    brief = Brief.query.filter(
        Brief.id == brief_id
    ).first_or_404()
    if brief.status == 'draft':
        brief_user_ids = [user.id for user in brief.users]
        if hasattr(current_user, 'role') and current_user.role == 'buyer' and current_user.id in brief_user_ids:
            return jsonify(brief.serialize(with_users=True))
        else:
            return forbidden("Unauthorised to view brief or brief does not exist")
    else:
        return jsonify(brief.serialize(with_users=False))


@api.route('/brief/<int:brief_id>/responses', methods=['GET'])
@login_required
@role_required('supplier')
def get_brief_responses(brief_id):
    """All brief responses (role=supplier)
    ---
    tags:
      - "Brief"
    security:
      - basicAuth: []
    parameters:
      - name: brief_id
        in: path
        type: number
        required: true
    definitions:
      BriefResponses:
        properties:
          briefResponses:
            type: array
            items:
              id: BriefResponse
    responses:
      200:
        description: A list of brief responses
        schema:
          id: BriefResponses
      404:
        description: brief_id not found
    """
    brief = briefs.get(brief_id)
    if not brief:
        not_found("Invalid brief id '{}'".format(brief_id))

    brief_responses = brief_responses_service.get_brief_responses(brief_id, current_user.supplier_code)

    return jsonify(brief=brief.serialize(with_users=False), briefResponses=brief_responses)


@api.route('/brief/<int:brief_id>/sellers', methods=['GET'])
@login_required
@role_required('buyer')
def get_brief_responded_sellers(brief_id):
    """All sellers who responded to a now closed brief (role=buyer)
    ---
    tags:
      - "Brief"
    security:
      - basicAuth: []
    parameters:
      - name: brief_id
        in: path
        type: number
        required: true
    definitions:
      BriefResponses:
        properties:
          sellers:
            type: array
            items:
              id: BriefResponse
    responses:
      200:
        description: A list of sellers as brief responses
        schema:
          id: BriefResponses
      403:
        description: brief_id is not owned by the requesting user
      404:
        description: brief_id not found
    """
    brief = briefs.get(brief_id)
    if not brief:
        not_found("Invalid brief id '{}'".format(brief_id))

    brief_user_ids = [user.id for user in brief.users]
    if current_user.id not in brief_user_ids:
        return forbidden("Unauthorised to view brief or brief does not exist")

    if brief.status != 'closed':
        return forbidden("Brief is not closed")

    brief_responses = brief_responses_service.get_brief_responses(brief_id, None)

    return jsonify(brief=brief.serialize(with_users=False), sellers=brief_responses)


@api.route('/brief/<int:brief_id>/sellers/notify', methods=['POST'])
@login_required
@role_required('buyer')
def notify_brief_sellers_unsuccessful(brief_id):
    """Send an email to sellers (role=buyers)
    ---
    tags:
      - "Brief"
    security:
      - basicAuth: []
    consumes:
      - application/json
    parameters:
      - name: brief_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          id: SellerNotification
          required:
            - subject
            - content
            - selectedSellers
          properties:
            subject:
              type: string
            content:
              type: string
            selectedSellers:
              type: array
              items:
                type: object
                required:
                  - supplier_code
                  - supplier_name
                  - contact_name
                properties:
                  supplier_code:
                    type: integer
                  supplier_name:
                    type: string
                  contact_name:
                    type: string
    responses:
      204:
        description: The email was successfully sent
      400:
        description: request body was missing required data
      403:
        description: brief_id is not owned by the requesting user
      404:
        description: brief_id not found
      500:
        description: the server failed to send the email
    """
    brief = briefs.get(brief_id)
    if not brief:
        not_found("Invalid brief id '{}'".format(brief_id))

    brief_user_ids = [user.id for user in brief.users]
    if current_user.id not in brief_user_ids:
        return forbidden("Unauthorised to view brief or brief does not exist")

    if brief.status != 'closed':
        return forbidden("Brief is not closed")

    request_body = get_json_from_request()
    try:
        subject = request_body['subject']
        content = request_body['content']
        notification_type = request_body['flow']
        supplier_codes = [supplier['supplier_code'] for supplier in request_body['selectedSellers']]
    except KeyError as e:
        rollbar.report_exc_info()
        return jsonify(errorMessage='The "{}" value was not found but is required'.format(e)), 400

    if not supplier_codes:
        return jsonify(errorMessage='You must supply at least one supplier to notify'), 400

    valid_types = ['unsuccessful']
    if notification_type not in valid_types:
        return jsonify(errorMessage='This flow type is not valid'), 400

    try:
        suppliers_to_notify = suppliers.get_all_by_code(supplier_codes)
        brief_responses = brief_responses_service.get_brief_responses(brief_id, None)
        valid_supplier_codes = [brief_response['supplier_code'] for brief_response in brief_responses]
        valid_suppliers = [supplier for supplier in suppliers_to_notify if supplier.code in valid_supplier_codes]
        if not valid_suppliers:
            return jsonify(errorMessage='You must supply at least one supplier to notify'), 400
        for supplier in valid_suppliers:
            send_seller_email(supplier, subject=subject, content=content)

    except Exception as e:
        rollbar.report_exc_info()
        return jsonify(errorMessage=e), 500

    audit = AuditEvent(
        audit_type=audit_types.notify_brief_responders,
        user=current_user.email_address,
        data={
            'briefId': brief_id,
            'notificationType': notification_type,
            'supplierCodesNotified': valid_supplier_codes
        },
        db_object=brief,
    )
    audit_service.log_audit_event(audit, {'audit_type': audit_types.notify_brief_responders,
                                          'briefId': brief_id})
    return ('', 204)


@api.route('/brief/<int:brief_id>/respond/documents/<string:supplier_code>/<slug>', methods=['POST'])
@login_required
def upload_brief_response_file(brief_id, supplier_code, slug):
    supplier, brief = _can_do_brief_response(brief_id)
    return jsonify({"filename": s3_upload_file_from_request(request, slug,
                                                            os.path.join(brief.framework.slug, 'documents',
                                                                         'brief-' + str(brief_id),
                                                                         'supplier-' + str(supplier.code)))
                    })


@api.route('/brief/<int:brief_id>/respond/documents/<int:supplier_code>/<slug>', methods=['GET'])
@login_required
def download_brief_response_file(brief_id, supplier_code, slug):
    brief = Brief.query.filter(
        Brief.id == brief_id
    ).first_or_404()
    brief_user_ids = [user.id for user in brief.users]
    if hasattr(current_user, 'role') and (current_user.role == 'buyer' and current_user.id in brief_user_ids) \
            or (current_user.role == 'supplier' and current_user.supplier_code == supplier_code):
        file = s3_download_file(slug, os.path.join(brief.framework.slug, 'documents',
                                                   'brief-' + str(brief_id),
                                                   'supplier-' + str(supplier_code)))

        mimetype = mimetypes.guess_type(slug)[0] or 'binary/octet-stream'
        return Response(file, mimetype=mimetype)
    else:
        return forbidden("Unauthorised to view brief or brief does not exist")


@api.route('/brief/<int:brief_id>/respond', methods=["POST"])
@login_required
def post_brief_response(brief_id):

    brief_response_json = get_json_from_request()
    supplier, brief = _can_do_brief_response(brief_id)
    try:
        brief_response = BriefResponse(
            data=brief_response_json,
            supplier=supplier,
            brief=brief
        )

        brief_response.validate()
        db.session.add(brief_response)
        db.session.flush()

    except ValidationError as e:
        brief_response_json['brief_id'] = brief_id
        rollbar.report_exc_info(extra_data=brief_response_json)
        message = ""
        if 'essentialRequirements' in e.message and e.message['essentialRequirements'] == 'answer_required':
            message = "Essential requirements must be completed"
            del e.message['essentialRequirements']
        if len(e.message) > 0:
            message += json.dumps(e.message)
        return jsonify(errorMessage=message), 400
    except Exception as e:
        brief_response_json['brief_id'] = brief_id
        rollbar.report_exc_info(extra_data=brief_response_json)
        return jsonify(errorMessage=e.message), 400

    try:
        send_brief_response_received_email(supplier, brief, brief_response)
    except Exception as e:
        brief_response_json['brief_id'] = brief_id
        rollbar.report_exc_info(extra_data=brief_response_json)

    audit = AuditEvent(
        audit_type=audit_types.create_brief_response,
        user=current_user.email_address,
        data={
            'briefResponseId': brief_response.id,
            'briefResponseJson': brief_response_json,
        },
        db_object=brief_response,
    )
    audit_service.log_audit_event(audit, {'audit_type': audit_types.create_brief_response,
                                          'briefResponseId': brief_response.id})

    return jsonify(briefResponses=brief_response.serialize()), 201


@api.route('/framework/<string:framework_slug>', methods=["GET"])
def get_framework(framework_slug):
    framework = Framework.query.filter(
        Framework.slug == framework_slug
    ).first_or_404()

    return jsonify(framework.serialize())
