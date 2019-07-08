from flask import current_app
from flask_login import current_user

from app.api.services import (audit_service, audit_types, team_members, teams,
                              users)

from .util import render_email_template, send_or_handle_error


def send_team_lead_notification_emails(team_id, user_ids=None):
    team = teams.find(id=team_id).first()

    if user_ids is None or len(user_ids) == 0:
        # Team leads added through the create flow
        team_leads = team_members.find(team_id=team_id, is_team_lead=True).all()
    else:
        # Team leads added through the edit flow
        team_leads = team_members.get_team_leads_by_user_id(user_ids)

    to_addresses = []
    for team_lead in team_leads:
        user = users.get(team_lead.user_id)
        to_addresses.append(user.email_address)

    email_body = render_email_template(
        'team_lead_added.md',
        frontend_url=current_app.config['FRONTEND_ADDRESS']
    )

    subject = 'You have been upgraded to a team lead'

    send_or_handle_error(
        to_addresses,
        email_body,
        subject,
        current_app.config['DM_GENERIC_NOREPLY_EMAIL'],
        current_app.config['DM_GENERIC_SUPPORT_NAME'],
        event_description_for_errors='team lead added email'
    )

    audit_service.log_audit_event(
        audit_type=audit_types.team_lead_added,
        data={
            'to_address': to_addresses
        },
        db_object=team,
        user=''
    )


def send_team_member_notification_emails(team_id, user_ids=None):
    team = teams.find(id=team_id).first()

    if user_ids is None or len(user_ids) == 0:
        # Team members added through the create flow
        members = team_members.find(team_id=team_id, is_team_lead=False).all()
    else:
        # Team members added through the edit flow
        members = team_members.get_team_members_by_user_id(user_ids)

    to_addresses = []
    for member in members:
        user = users.get(member.user_id)
        to_addresses.append(user.email_address)

    email_body = render_email_template(
        'team_member_added.md',
        frontend_url=current_app.config['FRONTEND_ADDRESS'],
        team_lead=current_user.name,
        team_name=team.name
    )

    subject = '{} has invited you to join {}'.format(current_user.name, team.name)

    send_or_handle_error(
        to_addresses,
        email_body,
        subject,
        current_app.config['DM_GENERIC_NOREPLY_EMAIL'],
        current_app.config['DM_GENERIC_SUPPORT_NAME'],
        event_description_for_errors='team member added email'
    )

    audit_service.log_audit_event(
        audit_type=audit_types.team_member_added,
        data={
            'to_address': to_addresses,
            'subject': subject
        },
        db_object=team,
        user=''
    )
