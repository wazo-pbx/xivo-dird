# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Avencall
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

import flask
import json

from hamcrest import assert_that
from hamcrest import equal_to
from mock import Mock
from mock import patch
from xivo_dird.plugins.headers_view import HeadersViewPlugin
from xivo_dird.plugins.tests.base_http_view_test_case import BaseHTTPViewTestCase


class TestHeadersView(BaseHTTPViewTestCase):

    def setUp(self):
        self.http_app = flask.Flask(__name__)
        self.plugin = HeadersViewPlugin()

    def test_that_load_add_the_route(self):
        args = {'http_app': self.http_app,
                'config': {}}

        self.plugin.load(args)

        route = '/{version}/directories/lookup/<profile>/headers'.format(
            version=HeadersViewPlugin.API_VERSION)

        self.assert_has_route(self.http_app, route)

    @patch('xivo_dird.plugins.headers_view.make_response')
    def test_result(self, make_response):
        args = {
            'http_app': Mock(),
            'config': {'displays': {'display_1': [{'title': 'Firstname',
                                                   'type': None,
                                                   'default': 'Unknown',
                                                   'field': 'firstname'},
                                                  {'title': 'Lastname',
                                                   'type': None,
                                                   'default': 'ln',
                                                   'field': 'lastname'}],
                                    'display_2': [{'title': 'fn',
                                                   'type': 'some_type',
                                                   'default': 'N/A',
                                                   'field': 'firstname'},
                                                  {'title': 'ln',
                                                   'type': None,
                                                   'default': 'N/A',
                                                   'field': 'LAST'}]},
                       'profile_to_display': {'profile_1': 'display_1',
                                              'profile_2': 'display_2',
                                              'profile_3': 'display_1'}}
        }
        self.plugin.load(args)

        result = self.plugin._header('profile_2')

        expected_result = json.dumps({
            'column_headers': ['fn', 'ln'],
            'column_types': ['some_type', None],
        })
        assert_that(result, equal_to(make_response.return_value))
        make_response.assert_called_once_with(expected_result, 200)

    @patch('xivo_dird.plugins.headers_view.time', Mock(return_value='now'))
    @patch('xivo_dird.plugins.headers_view.make_response')
    def test_result_with_a_bad_profile(self, make_response):
        args = {
            'http_app': Mock(),
            'config': {'displays': {'display_1': [{'title': 'Firstname',
                                                   'type': None,
                                                   'default': 'Unknown',
                                                   'field': 'firstname'},
                                                  {'title': 'Lastname',
                                                   'type': None,
                                                   'default': 'ln',
                                                   'field': 'lastname'}],
                                    'display_2': [{'title': 'fn',
                                                   'type': 'some_type',
                                                   'default': 'N/A',
                                                   'field': 'firstname'},
                                                  {'title': 'ln',
                                                   'type': None,
                                                   'default': 'N/A',
                                                   'field': 'LAST'}]},
                       'profile_to_display': {'profile_1': 'display_1',
                                              'profile_2': 'display_2',
                                              'profile_3': 'display_1'}}
        }
        self.plugin.load(args)

        result = self.plugin._header('profile_XXX')

        expected_result = json.dumps({
            'reason': ['The lookup profile does not exist'],
            'timestamp': ['now'],
            'status_code': 404,
        })
        assert_that(result, equal_to(make_response.return_value))
        make_response.assert_called_once_with(expected_result, 404)
