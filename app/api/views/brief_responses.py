from flask import abort, jsonify
from flask_login import current_user, login_required
from app.api import api
from ...models import AuditEvent
from app.api.services import brief_responses_service, audit_service
from ...datetime_utils import utcnow
from dmapiclient.audit import AuditTypes
import rollbar


@api.route('/brief-response/<int:brief_response_id>/withdraw', methods=['POST'])
@login_required
def withdraw_brief_response(brief_response_id):
    """Withdraw brief responses (role=supplier)
    ---
    tags:
      - "Brief Responses"
    security:
      - basicAuth: []
    parameters:
      - name: brief_response_id
        in: path
        type: number
        required: true
    definitions:
      BriefResponse:
        type: object
        properties:
          id:
            type: number
          data:
            type: object
          brief_id:
            type: number
          supplier_code:
            type: number
    responses:
      200:
        description: Successfully withdrawn a candidate
      400:
        description: brief_response_id not found
    """
    brief_response = (brief_responses_service
                      .find(id=brief_response_id, supplier_code=current_user.supplier_code)
                      .one_or_none())

    withdrawn_at = utcnow()
    if brief_response:
        brief_response.withdrawn_at = withdrawn_at
        brief_responses_service.save(brief_response)
    else:
        abort(404)

    try:
        audit = AuditEvent(
            audit_type=AuditTypes.update_brief_response,
            user=current_user.email_address,
            data={
                'briefResponseId': brief_response.id,
                'withdrawn_at': withdrawn_at
            },
            db_object=brief_response
        )
        audit_service.save(audit)
    except Exception as e:
        extra_data = {'audit_type': AuditTypes.update_brief_response, 'briefResponseId': brief_response.id}
        rollbar.report_exc_info(extra_data=extra_data)

    return jsonify(briefResponses=brief_response.serialize()), 200


@api.route('/brief-response/<int:brief_response_id>', methods=['GET'])
@login_required
def get_brief_response(brief_response_id):
    """Get brief response (role=supplier)
    ---
    tags:
      - "Brief Responses"
    security:
      - basicAuth: []
    parameters:
      - name: brief_response_id
        in: path
        type: number
        required: true
    definitions:
      BriefResponse:
        type: object
        properties:
          id:
            type: number
          data:
            type: object
          brief_id:
            type: number
          supplier_code:
            type: number
    responses:
      200:
        description: A brief response on id
        schema:
          $ref: '#/definitions/BriefResponse'
      404:
        description: brief_response_id not found
    """

    brief_response = brief_responses_service.find(id=brief_response_id, supplier_code=current_user.supplier_code).one_or_none()

    if brief_response is None:
        abort(404)

    return jsonify(briefResponses=brief_response.serialize())
