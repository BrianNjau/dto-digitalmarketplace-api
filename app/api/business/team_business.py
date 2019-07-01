from flask_login import current_user

from app.api.helpers import abort, get_email_domain
from app.api.services import (team_member_permissions, team_members, teams,
                              users)
from app.models import TeamMemberPermission, permission_types


def get_team(team_id):
    team = teams.find(id=team_id).one_or_none()
    if not team:
        not_found('No team with id {} found'.format(team_id))

    domain = get_email_domain(current_user.email_address)
    team = teams.get_team(team_id)

    for user_id, team_member in team['teamMembers'].iteritems():
        missing_permissions = [permission for permission in permission_types
                               if permission not in team_member['permissions']]

        for permission in missing_permissions:
            team_member['permissions'][permission] = False

    team.update(domain=domain)

    return team


def update_team(data):
    update_team_information(data)
    update_team_leads_and_members(data)
    update_permissions(data)

    team = teams.get_team(data['id'])
    return team


def update_team_information(data):
    team_data = {
        'email_address': data['emailAddress'],
        'id': data['id'],
        'name': data['name']
    }

    team = teams.save_team(team_data)
    return team


def update_team_leads_and_members(data):
    incoming_team_leads = data.get('teamLeads', [])
    incoming_team_members = data.get('teamMembers', [])
    incoming_team_lead_ids = [int(team_lead_id) for team_lead_id in incoming_team_leads]
    incoming_team_member_ids = [int(team_member_id) for team_member_id in incoming_team_members]

    team = teams.get(data.get('id'))
    current_team_leads = team_members.find(team_id=team.id, is_team_lead=True)
    current_team_members = team_members.find(team_id=team.id, is_team_lead=False)
    current_team_lead_ids = [team_lead.user_id for team_lead in current_team_leads]
    current_team_member_ids = [team_member.user_id for team_member in current_team_members]

    team_members_to_promote = set(incoming_team_lead_ids) & set(current_team_member_ids)
    team_leads_to_demote = set(incoming_team_member_ids) & set(current_team_lead_ids)

    team_leads_to_add = set(incoming_team_lead_ids) - set(current_team_lead_ids) - set(team_members_to_promote)
    team_leads_to_remove = set(current_team_lead_ids) - set(incoming_team_lead_ids) - set(team_leads_to_demote)

    for user_id in team_leads_to_add:
        user = users.add_to_team(user_id, team)
        team_members.promote_to_team_lead(team_id=team.id, user_id=user.id)

    for user_id in team_leads_to_demote:
        team_members.demote_team_lead(team_id=team.id, user_id=user_id)

    for user_id in team_leads_to_remove:
        user = users.remove_from_team(user_id, team.id)

    team_members_to_add = set(incoming_team_member_ids) - set(current_team_member_ids) - set(team_leads_to_demote)
    team_members_to_remove = set(current_team_member_ids) - set(incoming_team_member_ids) - set(team_members_to_promote)

    for user_id in team_members_to_add:
        user = users.add_to_team(user_id, team)

    for user_id in team_members_to_promote:
        team_members.promote_to_team_lead(team_id=team.id, user_id=user_id)

    for user_id in team_members_to_remove:
        user = users.remove_from_team(user_id, team.id)

    return get_team(team.id)


def update_permissions(data):
    permissions = {
        'answerSellerQuestions': 'answer_seller_questions',
        'createDrafts': 'create_drafts',
        'createWorkOrders': 'create_work_orders',
        'downloadReportingData': 'download_reporting_data',
        'downloadResponses': 'download_responses',
        'publishOpportunities': 'publish_opportunities'
    }

    incoming_team_members = data.get('teamMembers', {})
    incoming_permissions = data.get('teamMembers', {})
    team_id = data.get('id')

    for user_id, incoming_team_member in incoming_team_members.iteritems():
        incoming_permissions = incoming_team_member.get('permissions', {})
        permissions_to_add = [permissions[permission] for permission, value in incoming_permissions.iteritems()
                              if value is True]
        permissions_to_remove = [permissions[permission] for permission, value in incoming_permissions.iteritems()
                                 if value is False]

        team_member = team_members.find(team_id=team_id, user_id=user_id).one_or_none()
        current_permissions = team_member_permissions.find(team_member_id=team_member.id).all()

        for permission in permissions_to_remove:
            permission_to_remove = team_member_permissions.find(
                team_member_id=team_member.id,
                permission=permission
            ).one_or_none()

            if permission_to_remove is not None:
                team_member_permissions.delete(permission_to_remove)

        for permission in permissions_to_add:
            permission_to_add = team_member_permissions.find(
                team_member_id=team_member.id,
                permission=permission
            ).one_or_none()

            if permission_to_add is None:
                team_member_permissions.save(TeamMemberPermission(
                    team_member_id=team_member.id,
                    permission=permission
                ))
