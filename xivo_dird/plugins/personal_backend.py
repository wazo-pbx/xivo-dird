# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 Avencall
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>

import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from xivo_dird import BaseSourcePlugin
from xivo_dird import make_result_class
from xivo_dird.core import database

logger = logging.getLogger(__name__)

Session = scoped_session(sessionmaker())


class PersonalBackend(BaseSourcePlugin):

    def load(self, config, search_engine=None):
        logger.debug('Loading personal source')

        unique_column = 'id'
        source_name = config['config']['name']
        format_columns = config['config'].get(self.FORMAT_COLUMNS, {})

        result_class = make_result_class(
            source_name,
            unique_column,
            format_columns,
            is_personal=True,
            is_deletable=True
        )
        self._SourceResult = lambda contact: result_class(self._remove_empty_values(contact))
        self._search_engine = search_engine or self._new_search_engine(config['config']['db_uri'],
                                                                       config['config'].get(self.SEARCHED_COLUMNS),
                                                                       config['config'].get(self.FIRST_MATCHED_COLUMNS))

    def search(self, term, args=None):
        logger.debug('Searching personal contacts with %s', term)
        user_uuid = args['xivo_user_uuid']
        matching_contacts = self._search_engine.find_personal_contacts(user_uuid, term)
        return self.format_contacts(matching_contacts)

    def first_match(self, term, args=None):
        logger.debug('First matching personal contacts with %s', term)
        user_uuid = args['xivo_user_uuid']
        matching_contacts = self._search_engine.find_first_personal_contact(user_uuid, term)
        for contact in self.format_contacts(matching_contacts):
            return contact

    def list(self, source_entry_ids, args):
        logger.debug('Listing personal contacts')
        user_uuid = args['token_infos']['xivo_user_uuid']
        matching_contacts = self._search_engine.list_personal_contacts(user_uuid, source_entry_ids)
        return self.format_contacts(matching_contacts)

    def format_contacts(self, contacts):
        return [self._SourceResult(contact) for contact in contacts]

    def _new_search_engine(self, db_uri, searched_columns, first_match_columns):
        engine = create_engine(db_uri)
        Session.configure(bind=engine)
        return database.PersonalContactSearchEngine(Session,
                                                    searched_columns,
                                                    first_match_columns)

    @staticmethod
    def _remove_empty_values(dict_):
        return {attribute: value for attribute, value in dict_.iteritems() if value}
