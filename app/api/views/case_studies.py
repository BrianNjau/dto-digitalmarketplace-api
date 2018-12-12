from flask import jsonify
from flask_login import current_user, login_required
from app.api import api
from app.api.helpers import (
    abort,
    role_required
)
from app.models import (
    CaseStudyAssessment,
    CaseStudyAssessmentDomainCriteria
)
from app.api.services import (
    case_studies_service
)
from app.utils import get_json_from_request


@api.route('/casestudy/<int:id>/assessment', methods=['GET'])
@login_required
@role_required('admin')
def get_case_study_assessments(id):
    """Get case study assessments (role=admin)
    ---
    tags:
      - "Case study"
    security:
      - basicAuth: []
    parameters:
      - name: id
        in: path
        type: int
        required: true
    definitions:
      CaseStudyAssessment:
        properties:
          id:
            type: integer
          comment:
            type: string
          user_id:
            type: integer
          comment:
            type: string
          staus:
            type: string
    responses:
      200:
        description: List of case study assessments
        schema:
          $ref: '#/definitions/CaseStudyAssessment'
    """
    assessments = case_studies_service.get_case_study_assessments(id)
    return jsonify(assessments), 200


@api.route('/casestudy/<int:id>/assessment', methods=['POST'])
@login_required
@role_required('admin')
def add_assessment(id):
    """Add a case study assessment (role=admin)
    ---
    tags:
      - "Case study"
    security:
      - basicAuth: []
    parameters:
      - name: id
        in: path
        type: int
        required: true
      - name: data
        in: body
        required: true
        schema:
          $ref: '#/definitions/CaseStudyAssessmentUpsert'
    definitions:
          CaseStudyAssessmentUpsert:
            properties:
              data:
                type: object
    responses:
      200:
        description: Saved case study assessment
        type: object
        schema:
          $ref: '#/definitions/CaseStudyAssessment'
    """
    try:
        json_payload = get_json_from_request()

        user_id = current_user.id
        existing_for_user = case_studies_service.get_case_study_assessments(id, user_id)

        if len(existing_for_user) > 0:
            pass

        approved_criterias = json_payload.get('approved_criterias', [])
        assessment = CaseStudyAssessment(
            case_study_id=id,
            user_id=user_id,
            comment=json_payload.get('comment'),
            status=json_payload.get('status'),
            approved_criterias=[
                CaseStudyAssessmentDomainCriteria(
                    domain_criteria_id=ac
                ) for ac in approved_criterias]
        )
        saved = case_studies_service.insert_assessment(assessment)
        return jsonify(saved), 200

    except Exception as error:
        return abort(error.message)
