# Copyright 2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from hamcrest import (
    assert_that,
    contains,
    contains_inanyorder,
    has_entries,
)

from wazo_dird_client import Client

from .base_dird_integration_test import (
    BaseDirdIntegrationTest,
    VALID_TOKEN,
)


class TestBackends(BaseDirdIntegrationTest):

    asset = 'all_routes'

    def setUp(self):
        super().setUp()
        host = 'localhost'
        port = self.service_port(9489, 'dird')
        self.client = Client(host, port, token=VALID_TOKEN, verify_certificate=False)

    def test_list(self):
        result = self.client.backends.list()
        assert_that(
            result,
            has_entries(
                total=6,
                filtered=6,
                items=contains_inanyorder(
                    has_entries(name='csv'),
                    has_entries(name='csv_ws'),
                    has_entries(name='dird_phonebook'),
                    has_entries(name='ldap'),
                    has_entries(name='personal'),
                    has_entries(name='wazo'),
                    # not sample which is disabled
                    # not unknown which is not installed
                )
            )
        )

        result = self.client.backends.list(search='a')
        assert_that(
            result,
            has_entries(
                total=6,
                filtered=3,
                items=contains_inanyorder(
                    has_entries(name='ldap'),
                    has_entries(name='personal'),
                    has_entries(name='wazo'),
                )
            )
        )

        result = self.client.backends.list(name='csv')
        assert_that(
            result,
            has_entries(
                total=6,
                filtered=1,
                items=contains_inanyorder(
                    has_entries(name='csv'),
                )
            )
        )

        result = self.client.backends.list(order='name', direction='asc')
        assert_that(
            result,
            has_entries(
                total=6,
                filtered=6,
                items=contains(
                    has_entries(name='csv'),
                    has_entries(name='csv_ws'),
                    has_entries(name='dird_phonebook'),
                    has_entries(name='ldap'),
                    has_entries(name='personal'),
                    has_entries(name='wazo'),
                )
            )
        )

        result = self.client.backends.list(order='name', direction='desc')
        assert_that(
            result,
            has_entries(
                total=6,
                filtered=6,
                items=contains(
                    has_entries(name='wazo'),
                    has_entries(name='personal'),
                    has_entries(name='ldap'),
                    has_entries(name='dird_phonebook'),
                    has_entries(name='csv_ws'),
                    has_entries(name='csv'),
                )
            )
        )

        result = self.client.backends.list(limit=2, offset=3)
        assert_that(
            result,
            has_entries(
                total=6,
                filtered=6,
                items=contains(
                    has_entries(name='ldap'),
                    has_entries(name='personal'),
                )
            )
        )

        result = self.client.backends.list(limit=2)
        assert_that(
            result,
            has_entries(
                total=6,
                filtered=6,
                items=contains(
                    has_entries(name='csv'),
                    has_entries(name='csv_ws'),
                )
            )
        )

        result = self.client.backends.list(offset=4)
        assert_that(
            result,
            has_entries(
                total=6,
                filtered=6,
                items=contains(
                    has_entries(name='personal'),
                    has_entries(name='wazo'),
                )
            )
        )
