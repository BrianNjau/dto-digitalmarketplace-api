from app.api.helpers import Service
from app.models import BriefQuestion, db


class BriefQuestionService(Service):
    __model__ = BriefQuestion

    def __init__(self, *args, **kwargs):
        super(BriefQuestionService, self).__init__(*args, **kwargs)
