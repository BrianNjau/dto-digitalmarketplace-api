from app.api.helpers import Service
from app.models import (
    CaseStudy,
    CaseStudyAssessment,
    CaseStudyAssessmentDomainCriteria,
    Supplier,
    db
)
from sqlalchemy import func


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

    def get_case_studies(self):
        case_study_query = (
            db
            .session
            .query(
                CaseStudy.id,
                func.count(CaseStudyAssessment.id).label('assessment_count')
            )
            .join(CaseStudyAssessment, isouter=True)
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
                case_study_query.c.assessment_count
            )
            .join(Supplier)
            .join(case_study_query, case_study_query.c.id == CaseStudy.id)
        )
        return [r._asdict() for r in query.all()]
