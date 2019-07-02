from sqlalchemy import and_, func

from app.api.helpers import Service
from app.models import Team, TeamMember, TeamMemberPermission, User, db


class TeamsService(Service):
    __model__ = Team

    def __init__(self, *args, **kwargs):
        super(TeamsService, self).__init__(*args, **kwargs)

    def create_team(self, user):
        team = Team(
            name='My team',
            status='created'
        )

        user.teams.append(team)
        db.session.add(team)
        db.session.commit()

        return team

    def save_team(self, data):
        team = self.find(id=data['id']).one_or_none()
        self.update(team, name=data['name'], email_address=data['email_address'])
        return team

    def get_team(self, team_id):
        team_leads = (db.session
                        .query(TeamMember.team_id, TeamMember.user_id, User.name, User.email_address)
                        .join(Team, Team.id == TeamMember.team_id)
                        .join(User, User.id == TeamMember.user_id)
                        .filter(Team.id == team_id,
                                TeamMember.is_team_lead.is_(True))
                        .subquery('team_leads'))

        aggregated_team_leads = (db.session
                                   .query(team_leads.columns.team_id,
                                          func.json_object_agg(
                                              team_leads.columns.user_id,
                                              func.json_build_object(
                                                  'emailAddress', team_leads.columns.email_address,
                                                  'name', team_leads.columns.name
                                              )
                                          ).label('teamLeads'))
                                   .group_by(team_leads.columns.team_id)
                                   .subquery('aggregated_team_leads'))

        team_members = (db.session
                          .query(
                              TeamMember.team_id,
                              TeamMember.user_id,
                              User.name,
                              User.email_address,
                              TeamMemberPermission.permission)
                          .join(Team, Team.id == TeamMember.team_id)
                          .join(User, User.id == TeamMember.user_id)
                          .join(TeamMemberPermission, TeamMemberPermission.team_member_id == TeamMember.id)
                          .filter(Team.id == team_id,
                                  TeamMember.is_team_lead.is_(False))
                          .group_by(
                              TeamMember.team_id,
                              TeamMember.user_id,
                              User.name,
                              User.email_address,
                              TeamMemberPermission.permission)
                          .subquery('team_members'))

        aggregated_permissions = (db.session
                                    .query(
                                        team_members.columns.team_id,
                                        team_members.columns.user_id,
                                        team_members.columns.name,
                                        func.json_object_agg(
                                            team_members.columns.permission, True
                                        ).label('permissions'))
                                    .group_by(
                                        team_members.columns.team_id,
                                        team_members.columns.user_id,
                                        team_members.columns.name)
                                    .subquery('aggregated_permissions'))

        aggregated_team_members = (db.session
                                     .query(team_members.columns.team_id,
                                            func.json_object_agg(
                                                team_members.columns.user_id,
                                                func.json_build_object(
                                                    'emailAddress', team_members.columns.email_address,
                                                    'name', team_members.columns.name,
                                                    'permissions', aggregated_permissions.columns.permissions)
                                            ).label('teamMembers'))
                                     .join(aggregated_permissions,
                                           aggregated_permissions.columns.user_id == team_members.columns.user_id)
                                     .group_by(team_members.columns.team_id)
                                     .subquery('aggregated_team_members'))

        team = (db.session
                  .query(Team.id, Team.name, Team.email_address.label('emailAddress'), Team.status,
                         aggregated_team_leads.columns.teamLeads, aggregated_team_members.columns.teamMembers)
                  .join(aggregated_team_leads, aggregated_team_leads.columns.team_id == Team.id, isouter=True)
                  .join(aggregated_team_members, aggregated_team_members.columns.team_id == Team.id, isouter=True)
                  .filter(Team.id == team_id)
                  .one_or_none())

        return team._asdict() if team else None