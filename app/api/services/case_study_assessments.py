from sqlalchemy import func
from app.api.helpers import Service
from app.models import (
    CaseStudyAssessment,
    CaseStudyAssessmentDomainCriteria,
    DomainCriteria,
    Supplier,
    User,
    db
)


class CaseStudyAssessmentService(Service):
    __model__ = CaseStudyAssessment

    def __init__(self, *args, **kwargs):
        super(CaseStudyAssessmentService, self).__init__(*args, **kwargs)

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

    def delete_assessment(self, case_study_assessment_id, assessment):
        casestudy_assessment = CaseStudyAssessment.query.filter(
            CaseStudyAssessment.id == case_study_assessment_id
        ).first_or_404()
        db.session.delete(casestudy_assessment)

        return self.commit_changes()

    def update_assessment(self, case_study_assessment_id, assessment):
        case_study_assessment = (
            db
            .session
            .query(CaseStudyAssessment)
            .join(CaseStudyAssessmentDomainCriteria, isouter=True)
            .filter(CaseStudyAssessment.id == case_study_assessment_id)
            .one_or_none()
        )

        if not case_study_assessment:
            return None

        selected_criterias = assessment.get('approved_criteria', [])
        to_add_ac = []
        for ac in case_study_assessment.approved_criterias:
            if ac.domain_criteria_id not in selected_criterias:
                db.session.delete(ac)

        for sc in selected_criterias:
            dcs = [ac.domain_criteria_id for ac in case_study_assessment.approved_criterias]
            if sc not in dcs:
                db.session.add(
                    CaseStudyAssessmentDomainCriteria(
                        domain_criteria_id=sc,
                        case_study_assessment_id=case_study_assessment_id
                    )
                )

        return self.update(case_study_assessment, **assessment)
