# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from flask import current_app

from .util import render_email_template, send_or_handle_error

import rollbar


def send_brief_response_received_email(supplier, brief, brief_response):
    to_address = brief_response.data['respondToEmailAddress']

    if brief.lot.slug == 'rfx' or brief.lot.slug == 'atm':
        brief_url = current_app.config['FRONTEND_ADDRESS'] + '/2/' + brief.framework.slug + '/opportunities/' \
            + str(brief.id)
    else:
        brief_url = current_app.config['FRONTEND_ADDRESS'] + '/' + brief.framework.slug + '/opportunities/' \
            + str(brief.id)

    subject = "You've applied for {} successfully!"
    brief_title = brief.data['title']
    if len(brief_title) > 30:
        brief_title = '{}...'.format(brief_title[:30])
    subject = subject.format(brief_title)

    # prepare copy
    email_body = render_email_template(
        'brief_response_submitted.md',
        brief_url=brief_url,
        brief_title=brief_title,
        supplier_name=supplier.name,
        organisation=brief.data['organisation']
    )

    send_or_handle_error(
        to_address,
        email_body,
        subject,
        current_app.config['DM_GENERIC_NOREPLY_EMAIL'],
        current_app.config['DM_GENERIC_SUPPORT_NAME'],
        event_description_for_errors='brief response recieved'
    )


def send_brief_closed_email(brief):
    from app.api.services import audit_service, audit_types  # to circumvent circular dependency

    brief_email_sent_audit_event = audit_service.find(type=audit_types.sent_closed_brief_email.value,
                                                      object_type="Brief",
                                                      object_id=brief.id).count()

    if (brief_email_sent_audit_event > 0):
        return

    to_addresses = [user.email_address for user in brief.users if user.active]

    # prepare copy
    email_body = render_email_template(
        'brief_closed.md',
        frontend_url=current_app.config['FRONTEND_ADDRESS'],
        brief_name=brief.data['title'],
        brief_id=brief.id
    )

    subject = "Your brief has closed - please review all responses."

    send_or_handle_error(
        to_addresses,
        email_body,
        subject,
        current_app.config['DM_GENERIC_NOREPLY_EMAIL'],
        current_app.config['DM_GENERIC_SUPPORT_NAME'],
        event_description_for_errors='brief closed'
    )

    audit_service.log_audit_event(
        audit_type=audit_types.sent_closed_brief_email,
        user='',
        data={
            "to_addresses": ', '.join(to_addresses),
            "email_body": email_body,
            "subject": subject
        },
        db_object=brief)


def send_seller_requested_feedback_from_buyer_email(brief):
    from app.api.services import audit_service, audit_types  # to circumvent circular dependency

    to_addresses = [user.email_address for user in brief.users if user.active]

    # prepare copy
    email_body = render_email_template(
        'seller_requested_feedback_from_buyer_email.md',
        frontend_url=current_app.config['FRONTEND_ADDRESS'],
        brief_name=brief.data['title'],
        brief_id=brief.id
    )

    subject = "Buyer notifications to unsuccessful sellers"

    send_or_handle_error(
        to_addresses,
        email_body,
        subject,
        current_app.config['DM_GENERIC_NOREPLY_EMAIL'],
        current_app.config['DM_GENERIC_SUPPORT_NAME'],
        event_description_for_errors='seller_requested_feedback_from_buyer_email'
    )

    audit_service.log_audit_event(
        audit_type=audit_types.seller_requested_feedback_from_buyer_email,
        user='',
        data={
            "to_addresses": ', '.join(to_addresses),
            "email_body": email_body,
            "subject": subject
        },
        db_object=brief)


def send_seller_invited_to_rfx_email(brief, invited_supplier):
    from app.api.services import audit_service, audit_types  # to circumvent circular dependency

    to_addresses = []
    if 'contact_email' in invited_supplier.data:
        to_addresses = [invited_supplier.data['contact_email']]
    elif 'email' in invited_supplier.data:
        to_addresses = [invited_supplier.data['email']]

    if len(to_addresses) > 0:
        email_body = render_email_template(
            'brief_rfx_invite_seller.md',
            frontend_url=current_app.config['FRONTEND_ADDRESS'],
            brief_name=brief.data['title'],
            brief_id=brief.id
        )

        subject = "You have been invited to respond to an opportunity"

        send_or_handle_error(
            to_addresses,
            email_body,
            subject,
            current_app.config['DM_GENERIC_NOREPLY_EMAIL'],
            current_app.config['DM_GENERIC_SUPPORT_NAME'],
            event_description_for_errors='seller_invited_to_rfx_opportunity'
        )

        audit_service.log_audit_event(
            audit_type=audit_types.seller_invited_to_rfx_opportunity,
            user='',
            data={
                "to_addresses": ', '.join(to_addresses),
                "email_body": email_body,
                "subject": subject
            },
            db_object=brief)
