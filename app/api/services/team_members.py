from app.api.helpers import Service
from app.models import TeamMember


class TeamMembersService(Service):
    __model__ = TeamMember

    def __init__(self, *args, **kwargs):
        super(TeamMembersService, self).__init__(*args, **kwargs)

    def promote_to_team_lead(self, team_id, user_id):
        team_member = self.find(team_id=team_id, user_id=user_id).one_or_none()
        self.update(team_member, is_team_lead=True)

    def demote_team_lead(self, team_id, user_id):
        team_member = self.find(team_id=team_id, user_id=user_id).one_or_none()
        self.update(team_member, is_team_lead=False)
