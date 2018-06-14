from flask import jsonify, request
from flask_login import login_required

from app.api import api
from app.api.services import brief_assessors, users
from app.api.helpers import role_required, is_current_user_in_brief
from app.swagger import swag


@api.route('/brief/<int:brief_id>/assessors', methods=["GET"], endpoint='get_brief_assessors')
@login_required
@role_required('buyer')
@is_current_user_in_brief
def get(brief_id):
    """All brief assessors (role=buyer)
    ---
    tags:
      - brief
    security:
      - basicAuth: []
    parameters:
      - name: brief_id
        in: path
        type: number
        required: true
    definitions:
      BriefAssessors:
        type: array
        items:
          $ref: '#/definitions/BriefAssessor'
      BriefAssessor:
        type: object
        properties:
          id:
            type: integer
          brief_id:
            type: integer
          email_address:
            type: string
          view_day_rates:
            type: boolean
    responses:
      200:
        description: A list of brief assessors
        schema:
          $ref: '#/definitions/BriefAssessors'
    """
    assessors = brief_assessors.find(brief_id=brief_id)

    return jsonify([a.serializable for a in assessors])


@api.route('/assessors', methods=['POST'], endpoint='update_brief_assessors')
@login_required
@swag.validate('UpdateBriefAssessor')
@role_required('buyer')
@is_current_user_in_brief
def update():
    """Update brief assessors (role=buyer)
    ---
    tags:
      - assessors
    security:
      - basicAuth: []
    consumes:
      - application/json
    parameters:
      - name: body
        in: body
        required: true
        schema:
          id: UpdateBriefAssessor
          type: object
          required:
            - brief_id
            - email_address
            - view_day_rates
          properties:
            brief_id:
              type: integer
            email_address:
              type: string
            view_day_rates:
              type: boolean
    responses:
      200:
        description: An updated assessor
        schema:
          $ref: '#/definitions/BriefAssessor'
    """
    json_data = request.get_json()
    brief_id = json_data['brief_id']
    email_address = json_data['email_address']
    view_day_rates = json_data['view_day_rates']

    existing_user = users.first(email_address=email_address)

    if existing_user:
        assessor = brief_assessors.create(
            brief_id=brief_id,
            user_id=existing_user.id,
            view_day_rates=view_day_rates
        )
    else:
        assessor = brief_assessors.create(
            brief_id=brief_id,
            email_address=email_address,
            view_day_rates=view_day_rates
        )

    return jsonify(assessor.serializable)
