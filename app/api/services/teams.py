from app.api.helpers import Service
from app.models import Team, TeamMember, db


class TeamsService(Service):
    __model__ = Team

    def __init__(self, *args, **kwargs):
        super(TeamsService, self).__init__(*args, **kwargs)

    def create_team(self, user):
        team = Team(status='created')
        user.teams.append(team)

        db.session.add(team)
        db.session.commit()

        return team

    def save_team(self, data):
        team = self.find(id=data['id']).one_or_none()
        self.update(team, name=data['name'], email_address=data['emailAddress'])
        return team
