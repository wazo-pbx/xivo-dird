# -*- coding: utf-8 -*-

# Copyright (C) 2015 Avencall
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import logging
import urllib

PERSONAL_CONTACTS_KEY = 'xivo/private/{user_uuid}/contacts/personal/'
PERSONAL_CONTACT_KEY = 'xivo/private/{user_uuid}/contacts/personal/{contact_uuid}/'
PERSONAL_CONTACT_ATTRIBUTE_KEY = 'xivo/private/{user_uuid}/contacts/personal/{contact_uuid}/{attribute}'

logger = logging.getLogger(__name__)


def dict_from_consul(prefix, consul_dict):
    prefix_length = len(prefix)
    result = {}
    if consul_dict is None:
        return result
    for consul_kv in consul_dict:
        full_key = urllib.unquote(consul_kv['Key'])
        if full_key.startswith(prefix):
            key = full_key[prefix_length:]
            value = consul_kv['Value'].decode('utf-8') if consul_kv.get('Value') else None
            result[key] = value
    return result


def ls_from_consul(prefix, keys):
    keys = keys or []
    keys = (urllib.unquote(key) for key in keys)
    prefix_length = len(prefix)
    result = [key[prefix_length:].rstrip('/').decode('utf-8') for key in keys]
    return result


def dict_to_consul(prefix, dict_):
    prefix = prefix or ''
    dict_ = dict_ or {}
    result = {}
    for key, value in dict_.iteritems():
        full_key = urllib.quote('{}{}'.format(prefix.encode('utf-8'), key.encode('utf-8')))
        result[full_key] = value.encode('utf-8')
    return result
