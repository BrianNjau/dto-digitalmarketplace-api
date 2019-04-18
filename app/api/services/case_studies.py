from sqlalchemy import func
from sqlalchemy.dialects.postgresql import aggregate_order_by
from app.api.helpers import Service
from app.models import (
    CaseStudy,
    CaseStudyAssessment,
    CaseStudyAssessmentDomainCriteria,
    DomainCriteria,
    Supplier,
    User,
    db
)


class CaseStudyService(Service):
    __model__ = CaseStudy

    def __init__(self, *args, **kwargs):
        super(CaseStudyService, self).__init__(*args, **kwargs)

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

    def get_case_studies(self, search=None, case_study_id=None):
        case_study_assessment_query = (
            db
            .session
            .query(
                CaseStudyAssessmentDomainCriteria.case_study_assessment_id,
                func.array_agg(
                    func.json_build_object(
                        'domain_criteria_id', CaseStudyAssessmentDomainCriteria.domain_criteria_id,
                        'domain_criteria', DomainCriteria.name
                    )
                ).label('criterias_met')
            )
            .join(DomainCriteria)
            .group_by(CaseStudyAssessmentDomainCriteria.case_study_assessment_id)
            .subquery()
        )
        case_study_query = (
            db
            .session
            .query(
                CaseStudy.id,
                func.count(CaseStudyAssessment.id).label('assessment_count'),
                func.array_agg(
                    aggregate_order_by(
                        func.json_build_object(
                            'id', CaseStudyAssessment.id,
                            'user_id', CaseStudyAssessment.user_id,
                            'username', User.name,
                            'status', CaseStudyAssessment.status,
                            'comment', CaseStudyAssessment.comment,
                            'criterias_met', case_study_assessment_query.c.criterias_met
                        ),
                        CaseStudyAssessment.id
                    )
                ).label('assessment_results')
            )
            .join(CaseStudyAssessment, isouter=True)
            .join(
                case_study_assessment_query,
                case_study_assessment_query.c.case_study_assessment_id == CaseStudyAssessment.id,
                isouter=True)
            .join(User, isouter=True)
            # .filter( CaseStudyAssessment.status == 'unassessed')
            .group_by(CaseStudy.id)
        )
        if not search and not case_study_id:
            case_study_query = case_study_query.filter(CaseStudy.status == 'unassessed')
        case_study_query = case_study_query.subquery()

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

            .order_by(CaseStudy.supplier_code, CaseStudy.data['service'].astext)
        )
        if case_study_id:
            query = query.filter(CaseStudy.id == int(case_study_id))
        elif search:
            try:
                query = query.filter(CaseStudy.supplier_code == int(search))
            except ValueError:
                query = query.filter(Supplier.name.ilike('%{}%'.format(search.encode('utf-8'))))

        return [r._asdict() for r in query.all()]
