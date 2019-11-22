from sqlalchemy import desc, func

from app import db
from app.api.helpers import Service
from app.models import BriefResponse, Supplier


class BriefResponsesService(Service):
    __model__ = BriefResponse

    def __init__(self, *args, **kwargs):
        super(BriefResponsesService, self).__init__(*args, **kwargs)

    def create_brief_response(self, supplier, brief, data=None):
        if not data:
            data = {}

        brief_response = BriefResponse(
            data=data,
            supplier=supplier,
            brief=brief
        )

        db.session.add(brief_response)
        db.session.commit()
        return brief_response

    def save_brief_response(self, brief_response):
        db.session.add(brief_response)
        db.session.commit()
        return brief_response

    def get_brief_responses(self, brief_id, supplier_code, submitted_only=False, include_withdrawn=False):
        query = (
            db.session.query(BriefResponse.created_at,
                             BriefResponse.submitted_at,
                             BriefResponse.id,
                             BriefResponse.brief_id,
                             BriefResponse.supplier_code,
                             BriefResponse.status,
                             BriefResponse.data['respondToEmailAddress'].label('respondToEmailAddress'),
                             BriefResponse.data['specialistGivenNames'].label('specialistGivenNames'),
                             BriefResponse.data['specialistSurname'].label('specialistSurname'),
                             Supplier.name.label('supplier_name'))
            .join(Supplier)
            .filter(
                BriefResponse.brief_id == brief_id,
                BriefResponse.withdrawn_at.is_(None)
            )
        )
        if supplier_code:
            query = query.filter(BriefResponse.supplier_code == supplier_code)
        if submitted_only:
            query = query.filter(BriefResponse.submitted_at.isnot(None))
        if not include_withdrawn:
            query = query.filter(BriefResponse.withdrawn_at.is_(None))
        query = query.order_by(BriefResponse.id.asc())

        return [r._asdict() for r in query.all()]

    def get_responses_to_zip(self, brief_id, slug):
        query = (
            db.session.query(BriefResponse)
                      .join(Supplier)
                      .filter(BriefResponse.brief_id == brief_id,
                              BriefResponse.withdrawn_at.is_(None),
                              BriefResponse.submitted_at.isnot(None))
                      .order_by(func.lower(Supplier.name))
        )

        if slug == 'digital-professionals':
            query = query.order_by(func.lower(BriefResponse.data['specialistName'].astext))
        elif slug == 'specialist':
            query = query.order_by(func.lower(BriefResponse.data['specialistGivenNames'].astext))

        return query.all()

    def get_suppliers_responded(self, brief_id):
        query = (
            db.session.query(
                BriefResponse.supplier_code,
                Supplier.name.label('supplier_name'))
            .distinct(BriefResponse.supplier_code, Supplier.name.label('supplier_name'))
            .join(Supplier)
            .filter(
                BriefResponse.brief_id == brief_id,
                BriefResponse.withdrawn_at.is_(None),
                BriefResponse.submitted_at.isnot(None)
            )
        )

        return [r._asdict() for r in query.all()]

    def get_all_attachments(self, brief_id):
        response_template_query = (
            db.session.query(BriefResponse.data['responseTemplate'].label('requirements'),
                             BriefResponse.brief_id.label('brief_id'))
            .filter(
                BriefResponse.brief_id == brief_id,
                BriefResponse.withdrawn_at.is_(None),
                BriefResponse.submitted_at.isnot(None)
            )
            .subquery()
        )

        written_proposal_query = (
            db.session.query(BriefResponse.data['writtenProposal'].label('proposal'),
                             BriefResponse.brief_id.label('brief_id'))
            .filter(
                BriefResponse.brief_id == brief_id,
                BriefResponse.withdrawn_at.is_(None),
                BriefResponse.submitted_at.isnot(None)
            )
            .subquery()
        )

        resume_query = (
            db.session.query(BriefResponse.data['resume'].label('resume'),
                             BriefResponse.brief_id.label('brief_id'))
            .filter(
                BriefResponse.brief_id == brief_id,
                BriefResponse.withdrawn_at.is_(None),
                BriefResponse.submitted_at.isnot(None)
            )
            .subquery()
        )

        query = (
            db.session.query(BriefResponse.data['attachedDocumentURL'].label('attachments'),
                             response_template_query.c.requirements,
                             written_proposal_query.c.proposal,
                             resume_query.c.resume,
                             BriefResponse.supplier_code,
                             Supplier.name.label('supplier_name'))
            .join(Supplier)
            .outerjoin(response_template_query, response_template_query.c.brief_id == brief_id)
            .outerjoin(written_proposal_query, written_proposal_query.c.brief_id == brief_id)
            .outerjoin(resume_query, resume_query.c.brief_id == brief_id)
            .filter(
                BriefResponse.brief_id == brief_id,
                BriefResponse.withdrawn_at.is_(None),
                BriefResponse.submitted_at.isnot(None)
            )
        )
        responses = [r._asdict() for r in query.all()]
        attachments = []
        for response in responses:
            if 'attachments' in response and response['attachments']:
                for attachment in response['attachments']:
                    attachments.append({
                        'supplier_code': response['supplier_code'],
                        'supplier_name': response['supplier_name'],
                        'file_name': attachment
                    })
            if 'requirements' in response and response['requirements']:
                for requirement in response['requirements']:
                    attachments.append({
                        'supplier_code': response['supplier_code'],
                        'supplier_name': response['supplier_name'],
                        'file_name': requirement
                    })
            if 'proposal' in response and response['proposal']:
                for p in response['proposal']:
                    attachments.append({
                        'supplier_code': response['supplier_code'],
                        'supplier_name': response['supplier_name'],
                        'file_name': p
                    })
        return attachments

    def get_metrics(self):
        brief_response_count = (
            db
            .session
            .query(
                func.count(BriefResponse.id)
            )
            .filter(
                BriefResponse.data.isnot(None),
                BriefResponse.withdrawn_at.is_(None),
                BriefResponse.submitted_at.isnot(None)
            )
            .scalar()
        )

        return {
            "brief_response_count": brief_response_count
        }
