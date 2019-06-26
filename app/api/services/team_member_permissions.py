from app.api.helpers import Service
from app.models import TeamMemberPermission


class TeamMemberPermissionsService(Service):
    __model__ = TeamMemberPermission

    def __init__(self, *args, **kwargs):
        super(TeamMemberPermissionsService, self).__init__(*args, **kwargs)
