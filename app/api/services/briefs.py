from app.api.helpers import Service
from app import db
from app.models import Brief, BriefResponse, Supplier


class BriefsService(Service):
    __model__ = Brief

    def __init__(self, *args, **kwargs):
        super(BriefsService, self).__init__(*args, **kwargs)

    def get_supplier_responses(self, code):
        responses = (db.session.query(BriefResponse.created_at,
                                      Brief.id, Brief.data['title'].astext.label('name'),
                                      Brief.closed_at)
                     .join(Brief)
                     .filter(BriefResponse.supplier_code == code)
                     .order_by(Brief.closed_at)
                     .all())

        return [r._asdict() for r in responses]

    def get_brief_responses(self, brief_id, supplier_code):
        responses = (db.session.query(BriefResponse.created_at,
                                      BriefResponse.data,
                                      BriefResponse.id,
                                      BriefResponse.brief_id,
                                      BriefResponse.supplier_code,
                                      Supplier.name.label('supplier_name'))
                     .join(Supplier)
                     .filter(BriefResponse.supplier_code == supplier_code, BriefResponse.brief_id == brief_id)
                     .all())

        return [r._asdict() for r in responses]
