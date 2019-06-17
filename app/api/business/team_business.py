from flask_login import current_user

from app.api.helpers import abort, get_email_domain
from app.api.services import team_members, teams, users


def get_team(team_id):
    team = teams.find(id=team_id).one_or_none()
    if not team:
        not_found('No team with id {} found'.format(team_id))

    domain = get_email_domain(current_user.email_address)
    serialized_team = team.serialize()
    serialized_team.update(domain=domain)

    return serialized_team


def update_team(data):
    stage = data.get('stage', None)
    team_data = data.get('team', None)

    if not stage:
        abort('Missing stage')

    if stage == 'about':
        team = update_team_information(team_data)

    if stage == 'leads':
        team = update_team_leads(team_data)

    return team


def update_team_information(data):
    team_data = {
        'email_address': data['emailAddress'],
        'id': data['id'],
        'name': data['name']
    }

    team = teams.save_team(team_data)
    return team


def update_team_leads(data):
    team_leads = data.get('teamLeads', [])
    team = teams.get(data.get('id'))

    for user_id in team_leads:
        user = users.add_to_team(user_id, team)
        team_members.set_team_lead(team_id=team.id, user_id=user.id)
