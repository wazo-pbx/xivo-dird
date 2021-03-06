# Copyright 2016-2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from wazo_dird.auth import required_acl
from wazo_dird.rest_api import LegacyAuthResource


class Config(LegacyAuthResource):

    _config_service = None

    @classmethod
    def configure(cls, config_service):
        cls._config_service = config_service

    @required_acl('dird.config.read')
    def get(self):
        config = self._config_service.get_current_config()
        return dict(config)
