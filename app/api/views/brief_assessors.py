from flask import jsonify, request
from flask_login import login_required

from app.api import api
from app.api.services import brief_assessors, users
from app.api.helpers import role_required, is_current_user_in_brief, abort
from app.swagger import swag
from app.models import db, BriefAssessor


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
        type: integer
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


@api.route('/brief/<int:brief_id>/assessors', methods=['POST'], endpoint='update_brief_assessors')
@login_required
@swag.validate('UpdateBriefAssessor')
@role_required('buyer')
@is_current_user_in_brief
def update(brief_id):
    """Update brief assessors (role=buyer)
    ---
    tags:
      - brief
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
          id: UpdateBriefAssessor
          required:
            - assessors
          properties:
            assessors:
              type: array
              items:
                type: object
                required:
                  - email_address
                properties:
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
    assessor_data = json_data['assessors']
    current_assessors = [a.serializable for a in brief_assessors.find(brief_id=brief_id)]

    assessors = []
    for a in assessor_data:
        if any(ca['email_address'] == a['email_address'] for ca in current_assessors):
            db.session.rollback()
            abort('{} has already been invited'.format(a['email_address']))

        existing_user = users.first(email_address=a['email_address'])

        if existing_user:
            assessor = BriefAssessor(
                brief_id=brief_id,
                user_id=existing_user.id,
                view_day_rates=a['view_day_rates']
            )
        else:
            assessor = BriefAssessor(
                brief_id=brief_id,
                email_address=a['email_address'],
                view_day_rates=a['view_day_rates']
            )
        db.session.add(assessor)
        assessors.append(assessor)

    db.session.commit()

    return jsonify([a.serializable for a in assessors])
