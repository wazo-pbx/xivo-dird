# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from contextlib import contextmanager
from hamcrest import (
    assert_that,
    calling,
    equal_to,
    has_entries,
    has_properties,
    not_,
)
from mock import ANY

from xivo_test_helpers.hamcrest.uuid_ import uuid_
from xivo_test_helpers.hamcrest.raises import raises

from .helpers.base import BaseDirdIntegrationTest
from .helpers.constants import (
    MAIN_TENANT,
    SUB_TENANT,
    UNKNOWN_UUID,
    VALID_TOKEN_MAIN_TENANT,
    VALID_TOKEN_SUB_TENANT,
)
from .helpers.fixtures import http as fixtures

HTTP_401 = has_properties(response=has_properties(status_code=401))
HTTP_404 = has_properties(response=has_properties(status_code=404))


class BaseConferenceCRUDTestCase(BaseDirdIntegrationTest):

    asset = 'all_routes'
    valid_body = {
        'name': 'conferences',
        'auth': {
            'key_file': '/path/to/the/key/file',
        }
    }

    @contextmanager
    def source(self, client, *args, **kwargs):
        source = client.conference_source.create(*args, **kwargs)
        try:
            yield source
        finally:
            self.client.conference_source.delete(source['uuid'])


class TestGet(BaseConferenceCRUDTestCase):

    @fixtures.conference_source()
    def test_get(self, source):
        response = self.client.conference_source.get(source['uuid'])
        assert_that(response, equal_to(source))

        assert_that(
            calling(self.client.conference_source.get).with_args(UNKNOWN_UUID),
            raises(Exception).matching(HTTP_404)
        )

    @fixtures.conference_source(token=VALID_TOKEN_MAIN_TENANT)
    @fixtures.conference_source(token=VALID_TOKEN_SUB_TENANT)
    def test_get_multi_tenant(self, sub, main):
        main_client = self.get_client(VALID_TOKEN_MAIN_TENANT)
        sub_client = self.get_client(VALID_TOKEN_SUB_TENANT)

        response = main_client.conference_source.get(sub['uuid'])
        assert_that(response, equal_to(sub))

        assert_that(
            calling(main_client.conference_source.get).with_args(
                main['uuid'], tenant_uuid=SUB_TENANT,
            ),
            raises(Exception).matching(HTTP_404),
        )

        assert_that(
            calling(sub_client.conference_source.get).with_args(main['uuid']),
            raises(Exception).matching(HTTP_404),
        )

        assert_that(
            calling(sub_client.conference_source.get).with_args(
                main['uuid'], tenant_uuid=MAIN_TENANT,
            ),
            raises(Exception).matching(HTTP_401),
        )


class TestPost(BaseConferenceCRUDTestCase):

    def test_post(self):
        try:
            self.client.conference_source.create({})
        except Exception as e:
            assert_that(e.response.status_code, equal_to(400))
            assert_that(
                e.response.json(),
                has_entries(
                    message=ANY,
                    error_id='invalid-data',
                    details=has_entries('auth', ANY),
                ),
            )
        else:
            self.fail('Should have raised')

        with self.source(self.client, self.valid_body):
            assert_that(
                calling(self.client.conference_source.create).with_args(self.valid_body),
                raises(Exception).matching(has_properties(response=has_properties(status_code=409)))
            )

    def test_multi_tenant(self):
        main_tenant_client = self.get_client(VALID_TOKEN_MAIN_TENANT)
        sub_tenant_client = self.get_client(VALID_TOKEN_SUB_TENANT)

        with self.source(main_tenant_client, self.valid_body) as result:
            assert_that(result, has_entries(uuid=uuid_(), tenant_uuid=MAIN_TENANT))

        with self.source(main_tenant_client, self.valid_body, tenant_uuid=SUB_TENANT) as result:
            assert_that(result, has_entries(uuid=uuid_(), tenant_uuid=SUB_TENANT))

        with self.source(sub_tenant_client, self.valid_body) as result:
            assert_that(result, has_entries(uuid=uuid_(), tenant_uuid=SUB_TENANT))

        assert_that(
            calling(
                sub_tenant_client.conference_source.create
            ).with_args(self.valid_body, tenant_uuid=MAIN_TENANT),
            raises(Exception).matching(has_properties(response=has_properties(status_code=401))),
        )

        with self.source(main_tenant_client, self.valid_body):
            assert_that(
                calling(sub_tenant_client.conference_source.create).with_args(self.valid_body),
                not_(raises(Exception)),
            )
