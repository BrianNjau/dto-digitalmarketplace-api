from app.api.services import teams


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
