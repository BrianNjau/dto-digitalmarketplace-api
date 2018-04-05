from app.api.helpers import Service
from app.models import Supplier
from app import db


class SuppliersService(Service):
    __model__ = Supplier

    def __init__(self, *args, **kwargs):
        super(SuppliersService, self).__init__(*args, **kwargs)

    def get_all_by_code(self, codes):
        suppliers = (
            db.session.query(Supplier)
            .filter(Supplier.code.in_(codes))
            .all()
        )

        return suppliers
