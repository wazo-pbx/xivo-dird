# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from wazo_dird.helpers import BaseBackendView

from . import http


class ConferenceViewPlugin(BaseBackendView):

    backend = 'conference'
    list_resource = http.ConferenceList
    item_resource = http.ConferenceItem
