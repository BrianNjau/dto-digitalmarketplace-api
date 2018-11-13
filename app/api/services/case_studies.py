from sqlalchemy import func
from app.api.helpers import Service
from app.models import (
    CaseStudy,
    CaseStudyAssessment,
    CaseStudyAssessmentDomainCriteria,
    Supplier,
    User,
    db
)


class CaseStudyService(Service):
    __model__ = CaseStudy

    def __init__(self, *args, **kwargs):
        super(CaseStudyService, self).__init__(*args, **kwargs)

    def add_assessment(self, assessment):
        case_study_assessment = CaseStudyAssessment(
            status=assessment.get('status'),
            comment=assessment.get('comment'),
            user_id=assessment.get('user_id'),
            case_study_id=assessment.get('case_study_id'),
            approved_criterias=[
                CaseStudyAssessmentDomainCriteria(
                    domain_criteria_id=a
                ) for a in assessment.get('approved_criteria', [])
            ]
        )
        db.session.add(case_study_assessment)
        return self.commit_changes()

    def get_case_study_assessments(self, case_study_id=None, user_id=None):
        query = (
            db
            .session
            .query(CaseStudyAssessment.id)
            .filter(CaseStudyAssessment.case_study_id == case_study_id)
        )

        if user_id:
            query = query.filter(CaseStudyAssessment.user_id == user_id)

        results = (
            query
            .order_by(CaseStudyAssessment.id)
            .all()
        )

        return [r._asdict() for r in results]

    def get_case_study_assessment(self, case_study_assessment_id):
        result = (
            db
            .session
            .query(
                CaseStudyAssessment.id,
                CaseStudyAssessment.comment,
                CaseStudyAssessment.status,
                func.json_build_object(
                    'id', User.id,
                    'username', User.name
                ).label('user'),
                func.json_build_array(
                    CaseStudyAssessmentDomainCriteria.domain_criteria_id
                ).label('approved_criterias'),
                func.json_build_object(
                    'id', CaseStudy.id,
                    'supplier_code', CaseStudy.supplier_code,
                    'data', CaseStudy.data,
                    'status', CaseStudy.status
                ).label('case_study')
            )
            .join(CaseStudyAssessmentDomainCriteria, isouter=True)
            .join(User)
            .join(CaseStudy)
            .filter(CaseStudyAssessment.id == case_study_assessment_id)
            .one_or_none()
        )
        return result._asdict()

    def get_case_studies(self):
        case_study_query = (
            db
            .session
            .query(
                CaseStudy.id,
                func.count(CaseStudyAssessment.id).label('assessment_count'),
                func.array_agg(
                    func.json_build_object(
                        'user_id', CaseStudyAssessment.user_id,
                        'username', User.name,
                        'status', CaseStudyAssessment.status,
                        'comment', CaseStudyAssessment.comment
                    )
                ).label('assessment_results')
            )
            .join(CaseStudyAssessment, isouter=True)
            .join(User, isouter=True)
            .group_by(CaseStudy.id)
            .filter(CaseStudy.status == 'unassessed')
            # .having(func.count(CaseStudyAssessment.id) < 2)
            .subquery()
        )
        query = (
            db
            .session
            .query(
                CaseStudy.id,
                CaseStudy.data,
                CaseStudy.supplier_code,
                CaseStudy.status,
                CaseStudy.created_at,
                Supplier.name,
                case_study_query.c.assessment_count,
                case_study_query.c.assessment_results
            )
            .join(Supplier)
            .join(case_study_query, case_study_query.c.id == CaseStudy.id)
        )
        return [r._asdict() for r in query.all()]
