# Copyright 2019-2020 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import random
import requests
import string

from functools import wraps
from mockserver import MockServerClient as BaseMockServerClient

from ..constants import VALID_TOKEN_MAIN_TENANT


class UnVerifiedMockServerClient(BaseMockServerClient):
    def _put(self, endpoint, json=None):
        response = requests.put(self.url + endpoint, json=json, verify=False)
        return response


def random_string(length=10):
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))


def conference_source(**source_args):
    source_args.setdefault('name', random_string())
    source_args.setdefault('auth', {'key_file': '/path/to/key/file'})
    source_args.setdefault('token', VALID_TOKEN_MAIN_TENANT)

    def decorator(decorated):
        @wraps(decorated)
        def wrapper(self, *args, **kwargs):
            client = self.get_client(source_args['token'])
            source = client.conference_source.create(source_args)
            try:
                result = decorated(self, source, *args, **kwargs)
            finally:
                try:
                    self.client.conference_source.delete(source['uuid'])
                except requests.HTTPError as e:
                    response = getattr(e, 'response', None)
                    status_code = getattr(response, 'status_code', None)
                    if status_code != 404:
                        raise
            return result

        return wrapper

    return decorator


def csv_source(**source_args):
    def decorator(decorated):
        @wraps(decorated)
        def wrapper(self, *args, **kwargs):
            source_args.setdefault('name', random_string())
            source_args.setdefault('token', VALID_TOKEN_MAIN_TENANT)
            source_args.setdefault('file', '/tmp/fixture.csv')

            client = self.get_client(source_args['token'])
            source = client.csv_source.create(source_args)
            try:
                result = decorated(self, source, *args, **kwargs)
            finally:
                try:
                    self.client.csv_source.delete(source['uuid'])
                except requests.HTTPError as e:
                    response = getattr(e, 'response', None)
                    status_code = getattr(response, 'status_code', None)
                    if status_code != 404:
                        raise
            return result

        return wrapper

    return decorator


def csv_ws_source(**source_args):
    source_args.setdefault('lookup_url', 'http://example.com/fixture')
    source_args.setdefault('token', VALID_TOKEN_MAIN_TENANT)

    def decorator(decorated):
        @wraps(decorated)
        def wrapper(self, *args, **kwargs):
            client = self.get_client(source_args['token'])
            source = client.csv_ws_source.create(source_args)
            try:
                result = decorated(self, source, *args, **kwargs)
            finally:
                try:
                    self.client.csv_ws_source.delete(source['uuid'])
                except requests.HTTPError as e:
                    response = getattr(e, 'response', None)
                    status_code = getattr(response, 'status_code', None)
                    if status_code != 404:
                        raise
            return result

        return wrapper

    return decorator


def display(**display_args):
    display_args.setdefault('token', VALID_TOKEN_MAIN_TENANT)
    display_args.setdefault('name', 'display')
    display_args.setdefault('columns', [{'field': 'fn'}])

    def decorator(decorated):
        @wraps(decorated)
        def wrapper(self, *args, **kwargs):
            client = self.get_client(display_args['token'])
            display = client.displays.create(display_args)
            try:
                result = decorated(self, display, *args, **kwargs)
            finally:
                try:
                    self.client.displays.delete(display['uuid'])
                except requests.HTTPError as e:
                    response = getattr(e, 'response', None)
                    status_code = getattr(response, 'status_code', None)
                    if status_code != 404:
                        raise
            return result

        return wrapper

    return decorator


def google_result(contact_list, group_list=None):
    def decorator(decorated):
        @wraps(decorated)
        def wrapper(self, *args, **kwargs):
            google_port = self.service_port(443, 'google.com')
            mock_server = UnVerifiedMockServerClient(
                'https://localhost:{}'.format(google_port)
            )
            expectation = mock_server.create_expectation(
                '/m8/feeds/contacts/default/full', contact_list, 200
            )
            expectation['times']['unlimited'] = True
            mock_server.mock_any_response(expectation)

            if group_list:
                groups_expected = mock_server.create_expectation(
                    '/m8/feeds/groups/default/full', group_list, 200
                )
                groups_expected['times']['unlimited'] = True
                mock_server.mock_any_response(groups_expected)

            try:
                result = decorated(self, mock_server, *args, **kwargs)
            finally:
                mock_server.reset()
            return result

        return wrapper

    return decorator


def office365_result(contact_list):
    def decorator(decorated):
        @wraps(decorated)
        def wrapper(self, *args, **kwargs):
            office365_port = self.service_port(443, 'microsoft.com')
            mock_server = UnVerifiedMockServerClient(
                'http://localhost:{}'.format(office365_port)
            )
            count_expectation = mock_server.create_expectation(
                '/v1.0/me/contacts', {'@odata.count': len(contact_list)}, 200
            )
            count_expectation['httpRequest']['queryStringParameters'] = {
                '$count': ['true']
            }
            count_expectation['times']['unlimited'] = True
            mock_server.mock_any_response(count_expectation)

            expectation = mock_server.create_expectation(
                '/v1.0/me/contacts', contact_list, 200
            )
            expectation['times']['unlimited'] = True
            expectation['httpRequest']['queryStringParameters'] = {
                '$top': [str(len(contact_list))]
            }
            mock_server.mock_any_response(expectation)

            try:
                result = decorated(self, mock_server, *args, **kwargs)
            finally:
                mock_server.reset()
            return result

        return wrapper

    return decorator


def office365_error():
    def decorator(decorated):
        @wraps(decorated)
        def wrapper(self, *args, **kwargs):
            office365_port = self.service_port(443, 'microsoft.com')
            mock_server = UnVerifiedMockServerClient(
                'http://localhost:{}'.format(office365_port)
            )
            expectation = mock_server.create_expectation(
                '/v1.0/me/contacts/error', {}, 404
            )
            expectation['times']['unlimited'] = True
            mock_server.mock_any_response(expectation)

            try:
                result = decorated(self, mock_server, *args, **kwargs)
            finally:
                mock_server.reset()
            return result

        return wrapper

    return decorator


def google_source(**source_args):
    def decorator(decorated):
        @wraps(decorated)
        def wrapper(self, *args, **kwargs):
            source_args.setdefault('name', random_string())
            source_args.setdefault('token', VALID_TOKEN_MAIN_TENANT)
            source_args.setdefault(
                'auth', {'host': 'auth', 'port': 9497, 'prefix': None, 'https': False}
            )

            client = self.get_client(source_args['token'])
            source = client.backends.create_source(backend='google', body=source_args)

            try:
                result = decorated(self, source, *args, **kwargs)
            finally:
                try:
                    self.client.backends.delete_source('google', source['uuid'])
                except Exception as e:
                    response = getattr(e, 'response', None)
                    status_code = getattr(response, 'status_code', None)
                    if status_code != 404:
                        raise
            return result

        return wrapper

    return decorator


def office365_source(**source_args):
    def decorator(decorated):
        @wraps(decorated)
        def wrapper(self, *args, **kwargs):
            source_args.setdefault('name', random_string())
            source_args.setdefault('token', VALID_TOKEN_MAIN_TENANT)
            source_args.setdefault(
                'auth', {'host': 'auth', 'port': 9497, 'prefix': None, 'https': False}
            )
            source_args.setdefault(
                'endpoint', 'http://microsoft.com:443/v1.0/me/contacts'
            )

            client = self.get_client(source_args['token'])
            source = client.backends.create_source(
                backend='office365', body=source_args
            )

            try:
                result = decorated(self, source, *args, **kwargs)
            finally:
                try:
                    self.client.backends.delete_source('office365', source['uuid'])
                except Exception as e:
                    response = getattr(e, 'response', None)
                    status_code = getattr(response, 'status_code', None)
                    if status_code != 404:
                        raise
            return result

        return wrapper

    return decorator


def ldap_source(**source_args):
    source_args.setdefault('token', VALID_TOKEN_MAIN_TENANT)
    source_args.setdefault('ldap_uri', 'ldap://example.org')
    source_args.setdefault('ldap_base_dn', 'ou=people,dc=example,dc=org')

    def decorator(decorated):
        @wraps(decorated)
        def wrapper(self, *args, **kwargs):
            client = self.get_client(source_args['token'])
            source = client.ldap_source.create(source_args)
            try:
                result = decorated(self, source, *args, **kwargs)
            finally:
                try:
                    self.client.ldap_source.delete(source['uuid'])
                except requests.HTTPError as e:
                    response = getattr(e, 'response', None)
                    status_code = getattr(response, 'status_code', None)
                    if status_code != 404:
                        raise
            return result

        return wrapper

    return decorator


def personal_source(**source_args):
    source_args.setdefault('token', VALID_TOKEN_MAIN_TENANT)

    def decorator(decorated):
        @wraps(decorated)
        def wrapper(self, *args, **kwargs):
            client = self.get_client(source_args['token'])
            source = client.personal_source.create(source_args)
            try:
                result = decorated(self, source, *args, **kwargs)
            finally:
                try:
                    self.client.personal_source.delete(source['uuid'])
                except requests.HTTPError as e:
                    response = getattr(e, 'response', None)
                    status_code = getattr(response, 'status_code', None)
                    if status_code != 404:
                        raise
            return result

        return wrapper

    return decorator


def phonebook_source(**source_args):
    source_args.setdefault('token', VALID_TOKEN_MAIN_TENANT)

    def decorator(decorated):
        @wraps(decorated)
        def wrapper(self, *args, **kwargs):
            client = self.get_client(source_args['token'])
            source = client.phonebook_source.create(source_args)
            try:
                result = decorated(self, source, *args, **kwargs)
            finally:
                try:
                    self.client.phonebook_source.delete(source['uuid'])
                except requests.HTTPError as e:
                    response = getattr(e, 'response', None)
                    status_code = getattr(response, 'status_code', None)
                    if status_code != 404:
                        raise
            return result

        return wrapper

    return decorator


def wazo_source(**source_args):
    source_args.setdefault('auth', {'key_file': '/path/to/key/file'})
    source_args.setdefault('token', VALID_TOKEN_MAIN_TENANT)

    def decorator(decorated):
        @wraps(decorated)
        def wrapper(self, *args, **kwargs):
            client = self.get_client(source_args['token'])
            source = client.wazo_source.create(source_args)
            try:
                result = decorated(self, source, *args, **kwargs)
            finally:
                try:
                    self.client.wazo_source.delete(source['uuid'])
                except requests.HTTPError as e:
                    response = getattr(e, 'response', None)
                    status_code = getattr(response, 'status_code', None)
                    if status_code != 404:
                        raise
            return result

        return wrapper

    return decorator
