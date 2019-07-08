from app.api.helpers import Service
from app.models import TeamMember, db


class TeamMembersService(Service):
    __model__ = TeamMember

    def __init__(self, *args, **kwargs):
        super(TeamMembersService, self).__init__(*args, **kwargs)

    def get_team_leads_by_user_id(self, user_ids):
        return (db.session
                  .query(TeamMember)
                  .filter(
                      TeamMember.user_id.in_(user_ids),
                      TeamMember.is_team_lead.is_(True))
                  .all())

    def get_team_members_by_user_id(self, user_ids):
        return (db.session
                  .query(TeamMember)
                  .filter(
                      TeamMember.user_id.in_(user_ids),
                      TeamMember.is_team_lead.is_(False))
                  .all())

    def promote_to_team_lead(self, team_id, user_id):
        team_member = self.find(team_id=team_id, user_id=user_id).one_or_none()
        self.update(team_member, is_team_lead=True)

    def demote_team_lead(self, team_id, user_id):
        team_member = self.find(team_id=team_id, user_id=user_id).one_or_none()
        self.update(team_member, is_team_lead=False)
