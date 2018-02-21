from app.api.helpers import Service
from app import db
from app.models import BriefResponseContact


class BriefResponseContactService(Service):
    __model__ = BriefResponseContact

    def __init__(self, *args, **kwargs):
        super(BriefResponseContactService, self).__init__(*args, **kwargs)

    def get_all_by_brief_id(self, brief_ids):
        return db.session.query(BriefResponseContact).filter(BriefResponseContact.brief_id.in_(brief_ids)).all()
