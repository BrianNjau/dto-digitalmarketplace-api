from flask_login import current_user

from app.api.helpers import abort, get_email_domain
from app.api.services import teams


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

    return team


def update_team_information(data):
    team_data = {
        'email_address': data['emailAddress'],
        'id': data['id'],
        'name': data['name']
    }

    team = teams.save_team(team_data)
    return team
