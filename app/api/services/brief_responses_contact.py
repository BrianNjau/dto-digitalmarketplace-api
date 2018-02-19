from app.api.helpers import Service
from app import db
from app.models import BriefResponseContact


class BriefResponseContactService(Service):
    __model__ = BriefResponseContact

    def __init__(self, *args, **kwargs):
        super(BriefResponseContactService, self).__init__(*args, **kwargs)
