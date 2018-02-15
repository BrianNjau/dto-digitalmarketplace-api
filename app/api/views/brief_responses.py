from flask import abort, jsonify, make_response
from flask_login import current_user, login_required
from app.api import api
from ...models import BriefResponse, Supplier
from sqlalchemy.exc import DataError


@api.route('/brief-response/<int:brief_response_id>/withdraw', methods=['POST'])
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
      404:
        description: brief_response_id not found
    """
    return jsonify(success=True), 200

@api.route('/brief-response/<int:brief_response_id>', methods=['GET'])
@login_required
def get_brief_response(brief_response_id):
    """All brief responses (role=supplier)
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

    brief_response = BriefResponse.query.filter(
        BriefResponse.id == brief_response_id
    ).first_or_404()

    try:
        supplier = Supplier.query.filter(
            Supplier.code == current_user.supplier_code
        ).first()
    except DataError:
        supplier = None

    if not supplier:
        abort(make_response(jsonify(errorMessage="Invalid supplier Code '{}'".format(current_user.supplier_code)), 400))
    if supplier.code != brief_response.supplier_code:
        abort(make_response(jsonify(errorMessage="Unauthorised"), 403))

    return jsonify(briefResponses=brief_response.serialize())
