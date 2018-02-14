from app.api.helpers import Service
from app import db
from app.models import Brief, BriefResponse, BriefUser, AuditEvent, Framework, Lot, User, WorkOrder
from sqlalchemy import and_, case, func, or_
from sqlalchemy.sql.expression import case as sql_case
from sqlalchemy.sql.functions import concat
from sqlalchemy.types import Numeric
import pendulum


class BriefsService(Service):
    __model__ = Brief

    def __init__(self, *args, **kwargs):
        super(BriefsService, self).__init__(*args, **kwargs)

    def get_supplier_responses(self, code):
        responses = db.session.query(BriefResponse.created_at.label('response_date'),
                                     Brief.id, Brief.data['title'].astext.label('name'),
                                     Lot.name.label('framework'),
                                     Brief.closed_at,
                                     case([(AuditEvent.type == 'read_brief_responses', True)], else_=False)
                                     .label('is_downloaded'))\
            .distinct(Brief.closed_at, Brief.id)\
            .join(Brief, Lot)\
            .outerjoin(AuditEvent, and_(Brief.id == AuditEvent.data['briefId'].astext.cast(Numeric),
                                        AuditEvent.type == 'read_brief_responses'))\
            .filter(BriefResponse.supplier_code == code,
                    Brief.closed_at > pendulum.create(2018, 1, 1),
                    BriefResponse.withdrawn_at.is_(None)
                    )\
            .order_by(Brief.closed_at, Brief.id)\
            .all()

        return [r._asdict() for r in responses]

    def get_brief_responses(self, brief_id, supplier_code):
        responses = db.session.query(BriefResponse.created_at,
                                     BriefResponse.data,
                                     BriefResponse.id,
                                     BriefResponse.brief_id,
                                     BriefResponse.supplier_code)\
            .filter(BriefResponse.supplier_code == supplier_code, BriefResponse.brief_id == brief_id)\
            .all()

        return [r._asdict() for r in responses]
