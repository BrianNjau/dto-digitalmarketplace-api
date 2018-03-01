from flask import jsonify
from flask_login import current_user, login_required
from app.api import api
from app.api.helpers import not_found
from ...models import AuditEvent
from app.api.services import brief_response_contact_service, audit_service, audit_types
from app.api.helpers import role_required
from ...utils import get_json_from_request


@api.route('/brief-response-contact/<int:brief_id>', methods=['PUT'])
@login_required
@role_required('supplier')
def save_brief_response_contact(brief_id):
    """Save brief response contact (role=supplier)
    ---
    tags:
      - "Brief Response Contact"
    security:
      - basicAuth: []
    parameters:
      - name: brief_id
        in: path
        type: number
        required: true
      - name: body
        in: body
        required: true
        schema:
          id: BriefResponseContactSave
          required:
            - emailAddress
          properties:
            emailAddress:
              type: string
    responses:
      200:
        description: Successfully updated a candidate
        schema:
          id: BriefResponseContact
      404:
        description: brief_id not found
    """
    brief_response_contact = (brief_response_contact_service
                              .find(brief_id=brief_id,
                                    supplier_code=current_user.supplier_code)
                              .one_or_none())

    if brief_response_contact:
        brief_response_contact_json = get_json_from_request()
        brief_response_contact.email_address = brief_response_contact_json['emailAddress']
        brief_response_contact_service.save(brief_response_contact)

        audit = AuditEvent(
            audit_type=audit_types.update_brief_response_contact,
            user=current_user.email_address,
            data={
                'briefResponseContactId': brief_response_contact.id
            },
            db_object=brief_response_contact
        )
        audit_service.log_audit_event(audit, {'audit_type': audit_types.update_brief_response_contact,
                                              'briefResponseContactId': brief_response_contact.id})
    else:
        # there should only be a record when there is a brief response submitted by the supplier
        not_found('Cannot find brief response contact with brief_id :{} and supplier_code: {}'
                  .format(brief_id, current_user.supplier_code))

    return jsonify(brief_response_contact.serialize()), 200


@api.route('/brief-response-contact/<int:brief_id>', methods=['GET'])
@login_required
@role_required('supplier')
def get_brief_response_contact(brief_id):
    """Get brief response contact (role=supplier)
    ---
    tags:
      - "Brief Response Contact"
    security:
      - basicAuth: []
    parameters:
      - name: brief_id
        in: path
        type: number
        required: true
    definitions:
      BriefResponseContact:
        type: object
        properties:
          id:
            type: number
          email_address:
            type: string
          brief_id:
            type: number
          supplier_code:
            type: number
    responses:
      200:
        description: A brief response contact on id
        schema:
          id: BriefResponseContact
      404:
        description: brief_response_contact_id not found
    """

    brief_response_contact = brief_response_contact_service.find(brief_id=brief_id,
                                                                 supplier_code=current_user.supplier_code).one_or_none()

    if not brief_response_contact:
        not_found('Cannot find brief response contact with brief_id :{} and supplier_code: {}'
                  .format(brief_id, current_user.supplier_code))

    return jsonify(brief_response_contact.serialize())
