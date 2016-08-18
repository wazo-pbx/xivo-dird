# -*- coding: utf-8 -*-

# Copyright (C) 2016 Avencall
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

import unittest

from hamcrest import (assert_that,
                      calling,
                      contains,
                      contains_inanyorder,
                      equal_to,
                      raises)
from mock import Mock, sentinel as s

from xivo_dird import database
from xivo_dird.core.exception import (InvalidContactException,
                                      InvalidPhonebookException,
                                      InvalidTenantException)

from ..phonebook_service import (PhonebookServicePlugin as Plugin,
                                 _PhonebookService as Service)


class TestPhonebookServicePlugin(unittest.TestCase):

    def setUp(self):
        self.args = {'config': {'db_uri': s.db_uri}}

    def test_that_loading_without_a_proper_config_raises(self):
        plugin = Plugin()

        assert_that(calling(plugin.load).with_args({}),
                    raises(ValueError))
        assert_that(calling(plugin.load).with_args({'config': {}}),
                    raises(ValueError))


class _BasePhonebookServiceTest(unittest.TestCase):

    def setUp(self):
        self.phonebook_crud = Mock(database.PhonebookCRUD)
        self.contact_crud = Mock(database.PhonebookContactCRUD)
        self.service = Service(self.phonebook_crud,
                               self.contact_crud)


class TestPhonebookPhonebookAPI(_BasePhonebookServiceTest):

    def test_list_phonebook(self):
        result = self.service.list_phonebook('tenant')

        assert_that(result, equal_to(self.phonebook_crud.list.return_value))

    def test_create_phonebook(self):
        body = {'name': 'a name'}

        result = self.service.create_phonebook('tenant', body)

        self.phonebook_crud.create.assert_called_once_with('tenant', body)
        assert_that(result, equal_to(self.phonebook_crud.create.return_value))

    def test_count_phonebook(self):
        result = self.service.count_phonebook('tenant', param1=s.param1)

        self.phonebook_crud.count.assert_called_once_with('tenant', param1=s.param1)
        assert_that(result, equal_to(self.phonebook_crud.count.return_value))

    def test_that_create_with_no_name_raises(self):
        bodies = [{}, {'name': ''}, {'name': None}]
        for body in bodies:
            assert_that(calling(self.service.create_phonebook).with_args('tenant', body),
                        raises(InvalidPhonebookException))

    def test_edit_phonebook(self):
        body = {'name': 'foobar'}

        result = self.service.edit_phonebook('tenant', s.phonebook_id, body)

        self.phonebook_crud.edit.assert_called_once_with('tenant', s.phonebook_id, body)
        assert_that(result, equal_to(self.phonebook_crud.edit.return_value))

    def test_that_edit_with_no_name_raises(self):
        bodies = [{}, {'name': ''}, {'name': None}]
        for body in bodies:
            assert_that(calling(self.service.edit_phonebook).with_args('tenant', s.phonebook_id, body),
                        raises(InvalidPhonebookException))

    def test_delete_phonebook(self):
        self.service.delete_phonebook('tenant', s.phonebook_id)

        self.phonebook_crud.delete.assert_called_once_with('tenant', s.phonebook_id)

    def test_get_phonebook(self):
        result = self.service.get_phonebook('tenant', s.phonebook_id)

        assert_that(result, equal_to(self.phonebook_crud.get.return_value))
        self.phonebook_crud.get.assert_called_once_with('tenant', s.phonebook_id)

    def test_that_an_invalid_tenant_raises(self):
        body = {'name': 'foobar'}
        invalid_tenants = ['', '/', '%2F', u'é']
        for tenant in invalid_tenants:
            assert_that(calling(self.service.get_phonebook).with_args(tenant, s.phonebook_id),
                        raises(InvalidTenantException))
            assert_that(calling(self.service.list_phonebook).with_args(tenant),
                        raises(InvalidTenantException))
            assert_that(calling(self.service.count_phonebook).with_args(tenant),
                        raises(InvalidTenantException))
            assert_that(calling(self.service.create_phonebook).with_args(tenant, body),
                        raises(InvalidTenantException))
            assert_that(calling(self.service.edit_phonebook).with_args(tenant, s.phonebook_id, body),
                        raises(InvalidTenantException))
            assert_that(calling(self.service.delete_phonebook).with_args(tenant, s.phonebook_id),
                        raises(InvalidTenantException))


class TestPhonebookServiceContactAPI(_BasePhonebookServiceTest):

    def test_count_contact(self):
        result = self.service.count_contact('tenant', s.phonebook_id)

        assert_that(result, equal_to(self.contact_crud.count.return_value))
        self.contact_crud.count.assert_called_once_with('tenant', s.phonebook_id)

    def test_count_contact_with_a_search_param(self):
        result = self.service.count_contact('tenant', s.phonebook_id, search=s.search)

        assert_that(result, equal_to(self.contact_crud.count.return_value))
        self.contact_crud.count.assert_called_once_with('tenant', s.phonebook_id, search=s.search)

    def test_create_contact(self):
        body = {'firstname': 'foobar'}

        result = self.service.create_contact('tenant', s.phonebook_id, body)

        assert_that(result, equal_to(self.contact_crud.create.return_value))
        self.contact_crud.create.assert_called_once_with('tenant', s.phonebook_id, body)

    def test_that_the_id_field_should_be_ignored_on_create(self):
        result = self.service.create_contact('tenant', s.phonebook_id, {'firstname': 'bob',
                                                                        'id': s.uuid})

        assert_that(result, equal_to(self.contact_crud.create.return_value))
        self.contact_crud.create.assert_called_once_with('tenant', s.phonebook_id, {'firstname': 'bob'})

    def test_that_create_contact_raises_for_invalid_input(self):
        invalid_bodies = [{'': 'Foo'}, {}]
        for body in invalid_bodies:
            assert_that(calling(self.service.create_contact).with_args('tenant', s.phonebook_id, body),
                        raises(InvalidContactException))

    def test_edit_contact(self):
        body = {'firstname': 'Foobar'}
        result = self.service.edit_contact('tenant', s.phonebook_id, s.contact_uuid, body)

        assert_that(result, equal_to(self.contact_crud.edit.return_value))
        self.contact_crud.edit.assert_called_once_with('tenant', s.phonebook_id,
                                                       s.contact_uuid, body)

    def test_that_edit_contact_ignores_the_id_field(self):
        result = self.service.edit_contact('tenant', s.phonebook_id, s.contact_uuid,
                                           {'firstname': 'alice',
                                            'id': s.uuid})

        assert_that(result, equal_to(self.contact_crud.edit.return_value))
        self.contact_crud.edit.assert_called_once_with('tenant', s.phonebook_id,
                                                       s.contact_uuid, {'firstname': 'alice'})

    def test_that_edit_contact_raises_for_invalid_input(self):
        invalid_bodies = [{'': 'Foo'}, {}]
        for body in invalid_bodies:
            assert_that(calling(self.service.edit_contact)
                        .with_args('tenant', s.phonebook_id, s.contact_uuid, body),
                        raises(InvalidContactException))

    def test_delete_contact(self):
        result = self.service.delete_contact('tenant', s.phonebook_id, s.contact_uuid)

        assert_that(result, equal_to(self.contact_crud.delete.return_value))
        self.contact_crud.delete.assert_called_once_with('tenant', s.phonebook_id, s.contact_uuid)

    def test_get_contact(self):
        result = self.service.get_contact('tenant', s.phonebook_id, s.contact_uuid)

        assert_that(result, equal_to(self.contact_crud.get.return_value))
        self.contact_crud.get.assert_called_once_with('tenant', s.phonebook_id, s.contact_uuid)

    def test_that_an_invalid_tenant_raises(self):
        body = {'firstname': 'foobar'}
        invalid_tenants = ['', '/', '%2F', u'é']
        for tenant in invalid_tenants:
            assert_that(calling(self.service.get_contact).with_args(tenant, s.phonebook_id, s.contact_uuid),
                        raises(InvalidTenantException))
            assert_that(calling(self.service.list_contact).with_args(tenant, s.phonebook_id),
                        raises(InvalidTenantException))
            assert_that(calling(self.service.count_contact).with_args(tenant, s.phonebook_id),
                        raises(InvalidTenantException))
            assert_that(calling(self.service.create_contact).with_args(tenant, s.phonebook_id, body),
                        raises(InvalidTenantException))
            assert_that(calling(self.service.edit_contact)
                        .with_args(tenant, s.phonebook_id, s.contact_uuid, body),
                        raises(InvalidTenantException))
            assert_that(calling(self.service.delete_contact)
                        .with_args(tenant, s.phonebook_id, s.contact_uuid),
                        raises(InvalidTenantException))


class TestPhonebookServiceContactList(_BasePhonebookServiceTest):

    def setUp(self):
        super(TestPhonebookServiceContactList, self).setUp()
        self._manolo = {'firstname': 'Manolo', 'lastname': 'Laporte-Carpentier', 'number': '5551111234'}
        self._annabelle = {'firstname': 'Annabelle', 'lastname': 'Courval', 'number': '5552221234'}
        self._gary_bob = {'firstname': 'Gary-Bob', 'lastname': 'Derome'}
        self._antonin = {'firstname': 'Antonin', 'lastname': 'Mongeau', 'number': '5554441234'}
        self._simon = {'firstname': 'Simon', 'lastname': "L'Espérance"}
        self._contacts = [self._manolo, self._annabelle, self._gary_bob, self._antonin, self._simon]

    def test_that_list_returns_the_db_result_when_no_pagination_or_sorting(self):
        self.contact_crud.list.return_value = self._contacts

        result = self.service.list_contact('tenant', s.phonebook_id, search=s.search)

        self.contact_crud.list.assert_called_once_with('tenant', s.phonebook_id, search=s.search)
        assert_that(result, contains(*self._contacts))

    def test_that_list_can_be_limited(self):
        self.contact_crud.list.return_value = self._contacts

        result = self.service.list_contact('tenant', s.phonebook_id, search=s.search, limit=2)

        self.contact_crud.list.assert_called_once_with('tenant', s.phonebook_id, search=s.search)
        assert_that(result, contains(self._manolo, self._annabelle))

    def test_that_list_can_have_an_offset(self):
        self.contact_crud.list.return_value = self._contacts

        result = self.service.list_contact('tenant', s.phonebook_id, search=s.search, offset=3)

        self.contact_crud.list.assert_called_once_with('tenant', s.phonebook_id, search=s.search)
        assert_that(result, contains(self._antonin, self._simon))

    def test_that_limit_and_offset_work_togeter(self):
        self.contact_crud.list.return_value = self._contacts

        result = self.service.list_contact('tenant', s.phonebook_id, search=s.search, offset=1, limit=2)

        self.contact_crud.list.assert_called_once_with('tenant', s.phonebook_id, search=s.search)
        assert_that(result, contains(self._annabelle, self._gary_bob))

    def test_that_results_can_be_ordered(self):
        self.contact_crud.list.return_value = self._contacts

        result = self.service.list_contact('tenant', s.phonebook_id, search=s.search, order='firstname')

        self.contact_crud.list.assert_called_once_with('tenant', s.phonebook_id, search=s.search)
        assert_that(result, contains(self._annabelle,
                                     self._antonin,
                                     self._gary_bob,
                                     self._manolo,
                                     self._simon))

    def test_that_results_can_be_ordered_by_an_unknown_column_with_no_effect(self):
        self.contact_crud.list.return_value = self._contacts

        result = self.service.list_contact('tenant', s.phonebook_id, search=s.search,
                                           order='number', direction='desc')

        self.contact_crud.list.assert_called_once_with('tenant', s.phonebook_id, search=s.search)
        assert_that(result, contains_inanyorder(self._manolo,
                                                self._antonin,
                                                self._annabelle,
                                                self._gary_bob,  # no number
                                                self._simon))    # no number

    def test_that_the_direction_can_be_specified(self):
        self.contact_crud.list.return_value = self._contacts

        result = self.service.list_contact('tenant', s.phonebook_id, search=s.search,
                                           order='firstname', direction='desc')

        self.contact_crud.list.assert_called_once_with('tenant', s.phonebook_id, search=s.search)
        assert_that(result, contains(self._simon,
                                     self._manolo,
                                     self._gary_bob,
                                     self._antonin,
                                     self._annabelle))

    def test_all(self):
        self.contact_crud.list.return_value = self._contacts

        result = self.service.list_contact('tenant', s.phonebook_id,
                                           search=s.search,
                                           order='lastname', direction='desc',
                                           limit=3, offset=1)

        self.contact_crud.list.assert_called_once_with('tenant', s.phonebook_id, search=s.search)
        assert_that(result, contains(self._manolo, self._simon, self._gary_bob))
