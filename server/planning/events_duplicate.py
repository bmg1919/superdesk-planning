# -*- coding: utf-8; -*-
#
# This file is part of Superdesk.
#
# Copyright 2013, 2014 Sourcefabric z.u. and contributors.
#
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license

import logging
from superdesk import get_resource_service
from superdesk.resource import Resource
from superdesk.services import BaseService
from superdesk.metadata.utils import item_url
from flask import request
from .common import ITEM_STATE, WORKFLOW_STATE


logger = logging.getLogger(__name__)


class EventsDuplicateResource(Resource):
    endpoint_name = 'events_duplicate'
    resource_title = endpoint_name

    url = 'events/<{0}:item_id>/duplicate'.format(item_url)

    resource_methods = ['POST']
    item_methods = []

    privileges = {'POST': 'planning_event_management'}


class EventsDuplicateService(BaseService):
    def create(self, docs, **kwargs):
        history_service = get_resource_service('events_history')
        parent_id = request.view_args['item_id']

        parent_event = get_resource_service('events').find_one(req=None, _id=parent_id)

        new_event_ids = []
        for doc in docs:
            new_event = self._duplicate_doc(parent_event)
            new_ids = get_resource_service('events').post([new_event])
            history_service.on_item_created([new_event])
            new_event_ids = new_ids
            for new_id in new_ids:
                history_service.on_item_updated({'duplicate_id': new_id}, parent_event, 'duplicate')
            history_service.on_item_updated({'duplicate_id': parent_id}, new_event, 'duplicate_from')
        return new_event_ids

    def _duplicate_doc(self, original):
        new_doc = original.copy()

        for f in {'_id', 'guid', 'unique_name', 'unique_id', 'lock_user', 'lock_time',
                  'lock_session', 'lock_action', '_created', '_updated', '_etag', 'pubstatus'}:
            new_doc.pop(f, None)
        new_doc.get('dates').pop('recurring_rule', None)
        new_doc.pop('recurrence_id', None)
        new_doc.pop('previous_recurrence_id', None)
        new_doc[ITEM_STATE] = WORKFLOW_STATE.IN_PROGRESS
        eocstat_map = get_resource_service('vocabularies').find_one(req=None, _id='eventoccurstatus')
        if eocstat_map:
            new_doc['occur_status'] = [x for x in eocstat_map.get('items', []) if
                                       x['qcode'] == 'eocstat:eos5' and x.get('is_active', True)][0]
            new_doc['occur_status'].pop('is_active', None)

        return new_doc
