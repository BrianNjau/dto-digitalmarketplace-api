from sqlalchemy import and_, func, or_
from sqlalchemy.orm import joinedload, raiseload
from sqlalchemy.types import Integer

from app import db
from app.api.helpers import Service
from app.models import Brief, Domain, DomainCriteria, Evidence, EvidenceAssessment, Supplier


class EvidenceService(Service):
    __model__ = Evidence

    def __init__(self, *args, **kwargs):
        super(EvidenceService, self).__init__(*args, **kwargs)

    def get_domain_ids_with_evidence(self, supplier_code):
        query = (
            db.session.query(Evidence.domain_id)
            .filter(Evidence.supplier_code == supplier_code)
        )
        return [domain_id[0] for domain_id in query.distinct()]

    def get_evidence_by_id(self, evidence_id):
        query = (
            db.session.query(Evidence)
            .filter(
                Evidence.id == evidence_id
            )
            .options(
                joinedload(Evidence.supplier).joinedload(Supplier.signed_agreements),
                joinedload(Evidence.supplier).joinedload(Supplier.domains),
                joinedload(Evidence.user),
                joinedload(Evidence.brief).joinedload(Brief.clarification_questions),
                joinedload(Evidence.brief).joinedload(Brief.work_order),
                joinedload(Evidence.domain),
                raiseload('*')
            )
        )
        evidence = query.one_or_none()
        return evidence

    def get_latest_evidence_for_supplier_and_domain(self, domain_id, supplier_code):
        query = (
            db.session.query(Evidence)
            .filter(
                Evidence.supplier_code == supplier_code,
                Evidence.domain_id == domain_id
            )
            .options(
                joinedload(Evidence.supplier).joinedload(Supplier.signed_agreements),
                joinedload(Evidence.supplier).joinedload(Supplier.domains),
                joinedload(Evidence.user),
                joinedload(Evidence.brief).joinedload(Brief.clarification_questions),
                joinedload(Evidence.brief).joinedload(Brief.work_order),
                joinedload(Evidence.domain),
                raiseload('*')
            )
            .order_by(Evidence.id.desc())
        )
        evidence = query.first()
        return evidence

    def get_previous_submitted_evidence_for_supplier_and_domain(self, evidence_id, domain_id, supplier_code):
        query = (
            db.session.query(Evidence)
            .filter(
                Evidence.supplier_code == supplier_code,
                Evidence.domain_id == domain_id,
                Evidence.submitted_at.isnot(None),
                or_(Evidence.approved_at.isnot(None), Evidence.rejected_at.isnot(None)),
                Evidence.id != evidence_id
            )
            .options(
                joinedload(Evidence.supplier).joinedload(Supplier.signed_agreements),
                joinedload(Evidence.supplier).joinedload(Supplier.domains),
                joinedload(Evidence.user),
                joinedload(Evidence.brief).joinedload(Brief.clarification_questions),
                joinedload(Evidence.brief).joinedload(Brief.work_order),
                joinedload(Evidence.domain),
                raiseload('*')
            )
            .order_by(Evidence.id.desc())
        )
        evidence = query.first()
        return evidence

    def get_data(self, evidence_id):
        domain_criteria_id = (
            db.session.query(
                func.json_array_elements_text(Evidence.data['criteria']).label('dc_id')
            )
            .filter(Evidence.id == evidence_id)
            .subquery()
        )


        category_name = (
            db.session.query(
                Domain.name.label('category')
            )
            .join(Evidence, Evidence.domain_id == Domain.id)
            .filter(Evidence.id == evidence_id)
            .subquery()
        )

        category_name2 = (
            db.session.query(
                Domain.name.label('category'),
                Evidence.data['maxDailyRate'].label('maxDailyRate')
            )
            .join(Evidence, Evidence.domain_id == Domain.id)
            .filter(Evidence.id == evidence_id)
        )


        subquery = (
            db.session.query(
                domain_criteria_id.c.dc_id,
                DomainCriteria.name.label('domain_criteria_name'),
                Evidence.data['evidence'][domain_criteria_id.c.dc_id].label('evidence_data'),
            )
            .join(DomainCriteria, DomainCriteria.id == domain_criteria_id.c.dc_id.cast(Integer))
            .filter(Evidence.id == evidence_id)
            .subquery()
        )

        result = (
            db.session.query(
                # comment out category_name and maxDailtRate
                # using category_name 2 query to find out MaxdailyRate and add it
                # category_name,
                # Evidence.data['maxDailyRate'].label('maxDailyRate'),
                subquery
            )
            .filter(Evidence.id == evidence_id)
        )


# works but needs fixing up
        evidence_data = [evidence._asdict() for evidence in result.all()]
        evidence = {}
        evidence['evidence'] = evidence_data

        d = {}
        for c in category_name2.all():
            d = c._asdict()

        evidence['category'] = d.get("category")
        evidence['maxRate'] = d.get("maxDailyRate")

        return evidence

               # x = {}
        # for d in result.all():
        #     x = d._asdict()

        # #  store a local copy of category name
        # category_name = x.get("category")

        # # # remove all instances of category from evidence_data
        # x.pop('category')

        # test = {}
        # test['evidence'] = [x]

        # test['category_name'] = category_name
        # print('test')
        # print(test)

    def get_evidence_data(self, evidence_id):
        evidence_subquery = (
            db.session.query(
                Evidence.id.label('evidence_id'),
                func.json_array_elements_text(Evidence.data['criteria']).label('domain_criteria_id')
            )
            .filter(Evidence.id == evidence_id)
            .subquery()
        )

        subquery = (
            db.session.query(
                evidence_subquery.c.evidence_id,
                evidence_subquery.c.domain_criteria_id,
                DomainCriteria.name,
            )
            .join(DomainCriteria, DomainCriteria.id == evidence_subquery.c.domain_criteria_id.cast(Integer))
            .subquery()
        )

        domain_criteria_name = (
            db.session.query(
                subquery.c.evidence_id,
                func.json_object_agg(
                    subquery.c.domain_criteria_id,
                    func.json_build_object(
                        'name', subquery.c.name
                    )
                ).label('domain_criteria')
            )
            .group_by(subquery.c.evidence_id)
            .subquery()
        )

        category_name = (
            db.session.query(
                Domain.name.label('domain_name')
            )
            .join(Evidence, Evidence.domain_id == Domain.id)
            .filter(Evidence.id == evidence_id)
            .subquery()
        )

        evidence_assessment_status = (
            db.session.query(
                EvidenceAssessment.status.label('status')
            )
            .filter(evidence_id == EvidenceAssessment.evidence_id)
            .subquery()
        )

        query = (
            db.session.query(
                Evidence.id,
                Evidence.data['criteria'].label('criteria'),
                Evidence.data['evidence'].label('evidence_data'),
                Evidence.data['maxDailyRate'].label('maxDailyRate'),
                evidence_assessment_status.c.status,
                domain_criteria_name.c.domain_criteria,
                category_name.c.domain_name
            )
            .join(domain_criteria_name, domain_criteria_name.c.evidence_id == Evidence.id)
        )

        return [evidence._asdict() for evidence in query.all()]

    def get_all_evidence(self, supplier_code=None):
        query = (
            db.session.query(
                Evidence.id.label('id'),
                Evidence.status,
                Evidence.created_at,
                Evidence.submitted_at,
                Evidence.approved_at,
                Evidence.rejected_at,
                Evidence.data.label('data'),
                Evidence.data['maxDailyRate'].astext.label('maxDailyRate'),
                Supplier.name.label('supplier_name'), Supplier.code.label('supplier_code'),
                Brief.id.label('brief_id'), Brief.closed_at.label('brief_closed_at'),
                Brief.data['title'].astext.label('brief_title'),
                Domain.name.label('domain_name'), Domain.id.label('domain_id'),
                Domain.price_maximum.label('domain_price_maximum')
            )
            .join(Domain, Evidence.domain_id == Domain.id)
            .join(Supplier, Evidence.supplier_code == Supplier.code)
            .outerjoin(Brief, Evidence.brief_id == Brief.id)
            .order_by(Evidence.submitted_at.desc(), Evidence.created_at.desc())
        )
        if supplier_code:
            query = query.filter(Evidence.supplier_code == supplier_code)
        return [e._asdict() for e in query.all()]

    def get_all_submitted_evidence(self):
        query = (
            db.session.query(
                Evidence.id.label('id'), Evidence.submitted_at,
                Evidence.data.label('data'),
                Evidence.data['maxDailyRate'].astext.label('maxDailyRate'),
                Supplier.name.label('supplier_name'), Supplier.code.label('supplier_code'),
                Brief.id.label('brief_id'), Brief.closed_at.label('brief_closed_at'),
                Brief.data['title'].astext.label('brief_title'),
                Domain.name.label('domain_name'), Domain.id.label('domain_id'),
                Domain.price_maximum.label('domain_price_maximum')
            )
            .filter(
                Evidence.submitted_at.isnot(None),
                Evidence.approved_at.is_(None),
                Evidence.rejected_at.is_(None)
            )
            .join(Domain, and_(Evidence.domain_id == Domain.id))
            .join(Supplier, and_(Evidence.supplier_code == Supplier.code))
            .outerjoin(Brief, and_(Evidence.brief_id == Brief.id))
            .order_by(Evidence.submitted_at.asc())
        )
        return query.all()

    def get_approved_domain_criteria(self, evidence_id, previous_evidence_id):
        previous_rejected_criteria = (
            db.session
              .query(func.json_object_keys(EvidenceAssessment.data['failed_criteria']))
              .filter(EvidenceAssessment.evidence_id == previous_evidence_id)
              .subquery()
        )

        previous_submitted_criteria = (
            db.session
              .query(func.json_array_elements_text(Evidence.data['criteria']).label('id'))
              .filter(Evidence.id == previous_evidence_id)
              .subquery()
        )

        submitted_criteria = (
            db.session
              .query(func.json_array_elements_text(Evidence.data['criteria']).label('id'))
              .filter(Evidence.id == evidence_id)
              .subquery()
        )

        approved_criteria = (
            db.session
              .query(submitted_criteria.columns.id)
              .filter(
                  submitted_criteria.columns.id.notin_(previous_rejected_criteria),
                  submitted_criteria.columns.id.in_(previous_submitted_criteria))
              .all()
        )

        return [criteria.id for criteria in approved_criteria]

    def get_submitted_evidence(self, evidence_id):
        query = (
            db.session.query(
                Evidence.id.label('id'), Evidence.submitted_at,
                Evidence.data.label('data'),
                Evidence.data['maxDailyRate'].astext.label('maxDailyRate'),
                Supplier.name.label('supplier_name'), Supplier.code.label('supplier_code'),
                Brief.id.label('brief_id'), Brief.closed_at.label('brief_closed_at'),
                Brief.data['title'].astext.label('brief_title'),
                Domain.name.label('domain_name'), Domain.id.label('domain_id'),
                Domain.price_maximum.label('domain_price_maximum')
            )
            .filter(
                Evidence.submitted_at.isnot(None),
                Evidence.approved_at.is_(None),
                Evidence.rejected_at.is_(None),
                Evidence.id == evidence_id
            )
            .join(Domain, and_(Evidence.domain_id == Domain.id))
            .join(Supplier, and_(Evidence.supplier_code == Supplier.code))
            .outerjoin(Brief, and_(Evidence.brief_id == Brief.id))
            .order_by(Evidence.submitted_at.asc())
        )
        return query.one_or_none()

    def supplier_has_assessment_for_brief(self, supplier_code, brief_id):
        evidence = self.filter(
            Evidence.supplier_code == supplier_code,
            Evidence.brief_id == brief_id
        ).order_by(Evidence.id.desc()).first()
        return True if evidence else False

    def create_evidence(self, domain_id, supplier_code, user_id, brief_id=None, data=None, do_commit=True):
        if not data:
            data = {}
        evidence = Evidence(
            domain_id=domain_id,
            supplier_code=supplier_code,
            brief_id=brief_id,
            user_id=user_id,
            data=data
        )
        return self.save(evidence, do_commit)

    def save_evidence(self, evidence, do_commit=True):
        return self.save(evidence, do_commit)
