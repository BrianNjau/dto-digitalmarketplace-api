#!/usr/bin/env python2
import csv
import json
import logging

from utils import makeClient


def check_response(response, supplier):
    if response.status_code >= 400:
        msg = 'Error adding supplier {}: server returned code {} {}'.format(
            supplier['name'],
            response.status_code,
            response.get_data()
        )
        logging.error(msg)
        sys.exit(1)
    else:
        return json.loads(response.get_data())


def run_import(input_file, client):
    num_successes = 0

    for record in csv.DictReader(input_file):

        supplier = {
            'name': record['name'],
            'abn': record['abn'],
            'website': record['website'],
            'contact_name': record['business_contact_name'],
            'contact_phone': record['business_contact_phone'],
            'contact_email': record['business_contact_email'],
            'addresses': [{
                'address_line': record['address_line'],
                'suburb': record['suburb'],
                'state': record['state'],
                'postal_code': record['postal_code'],
                'country': record['country']
            }],
            'contacts': [{
                'name': record['auth_rep_name'],
                'email': record['auth_rep_email'],
                'phone': record['auth_rep_phone']
            }],
        }

        json_data = check_response(client.post('/api/suppliers', data=json.dumps({'supplier': supplier}),
                                   content_type='application/json'), supplier)
        supplier_code = json_data['supplier']['code']
        check_response(client.put('/api/suppliers/{}/frameworks/orams'.format(supplier_code),
                       data=json.dumps({'updated_by': ''}), content_type='application/json'), supplier)

        print '{}: {}'.format(supplier_code, supplier['name'])
        num_successes += 1


if __name__ == '__main__':
    import sys
    client = makeClient()

    run_import(sys.stdin, client)