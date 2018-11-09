from app.api.helpers import Service
from app.models import CaseStudy, CaseStudyAssessment, db


class CaseStudyService(Service):
    __model__ = CaseStudy

    def __init__(self, *args, **kwargs):
        super(CaseStudyService, self).__init__(*args, **kwargs)

    def insert_assessment(self, assessment):
        existing = self.find(key=key).one_or_none()
        if existing:
            saved = self.update(existing, data=data)
        else:
            saved = self.create(key=key, data=data)

        return {
            "key": saved.key,
            "data": saved.data,
            "updated_at": saved.updated_at
        } if saved else None

    def get_case_study_assessments(self, case_study_id, user_id=None):
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
