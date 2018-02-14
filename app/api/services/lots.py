from app.api.helpers import Service
from app import db
from app.models import Lot


class LotsService(Service):
    __model__ = Lot

    def __init__(self, *args, **kwargs):
        super(LotsService, self).__init__(*args, **kwargs)
