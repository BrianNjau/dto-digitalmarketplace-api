class ATMDataValidator(object):

    def __init__(self, brief):
        self.brief = brief

    def validate(self):
        errors = []

        try:
            # allowed fields and types
            whitelist = [
                {'name': 'id', 'type': int},
                {'name': 'title', 'type': basestring},
                {'name': 'organisation', 'type': basestring},
                {'name': 'location', 'type': list},
                {'name': 'summary', 'type': basestring},
                {'name': 'industryBriefing', 'type': basestring},
                {'name': 'sellers', 'type': dict},
                {'name': 'attachments', 'type': list},
                {'name': 'responseTemplate', 'type': list},
                {'name': 'evaluationType', 'type': list},
                {'name': 'proposalType', 'type': list},
                {'name': 'evaluationCriteria', 'type': list},
                {'name': 'includeWeightings', 'type': bool},
                {'name': 'closedAt', 'type': basestring},
                {'name': 'startDate', 'type': basestring},
                {'name': 'contractLength', 'type': basestring},
                {'name': 'contractExtensions', 'type': basestring},
                {'name': 'budgetRange', 'type': basestring},
                {'name': 'workingArrangements', 'type': basestring},
                {'name': 'publish', 'type': bool},
                {'name': 'sellerSelector', 'type': basestring},
                {'name': 'securityClearance', 'type': basestring},
                {'name': 'workAlreadyDone', 'type': basestring},
                {'name': 'endUsers', 'type': basestring},
                {'name': 'backgroundInformation', 'type': basestring},
                {'name': 'outcome', 'type': basestring},
                {'name': 'timeframeConstraints', 'type': basestring},
                {'name': 'contactNumber', 'type': basestring}
            ]

            request_keys = self.brief.data.keys()
            whitelisted_keys = [key['name'] for key in whitelist]
            for key in request_keys:
                if key not in whitelisted_keys:
                    errors.append('Unexpected field "%s"' % key)

            for key in whitelist:
                if key['name'] in request_keys and not isinstance(self.brief.data.get(key['name'], None), key['type']):
                    errors.append('Field "%s" is invalid, unexpected type' % key['name'])

        except Exception as e:
            errors.append(e.message)

        return errors
