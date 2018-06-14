from app.api.helpers import Service
from app.models import BriefAssessor


class BriefAssessorsService(Service):
    __model__ = BriefAssessor

    def __init__(self, *args, **kwargs):
        super(BriefAssessorsService, self).__init__(*args, **kwargs)
