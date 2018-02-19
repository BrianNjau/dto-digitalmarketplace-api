from app.api.helpers import Service
from app import db
from app.models import BriefResponse


class BriefResponsesService(Service):
    __model__ = BriefResponse

    def __init__(self, *args, **kwargs):
        super(BriefResponsesService, self).__init__(*args, **kwargs)
