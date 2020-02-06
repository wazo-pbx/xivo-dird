# Copyright 2019-2020 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging

from operator import itemgetter

import requests

from wazo_auth_client import Client as Auth

from .exceptions import GoogleTokenNotFoundException


logger = logging.getLogger(__name__)


class GoogleService:

    USER_AGENT = 'wazo_ua/1.0'
    contacts_url = 'https://google.com/m8/feeds/contacts/default/full'
    groups_url = 'https://google.com/m8/feeds/groups/default/full'

    def __init__(self):
        self.formatter = ContactFormatter()

    def get_contacts_with_term(self, google_token, term):
        for contact in self._fetch(google_token, term=term):
            yield contact

    def get_contacts(self, google_token, **list_params):
        contacts = list(self._fetch(google_token, term=list_params.get('search')))
        total = len(contacts)
        sorted_contacts = self._sort(contacts, **list_params)
        paginated_contacts = self._paginate(sorted_contacts, **list_params)
        return paginated_contacts, total

    def _fetch(self, google_token, term=None):
        headers = self.headers(google_token)
        group_id = self._get_my_contacts_group_id(headers)
        query_params = {'alt': 'json', 'max-results': 1000}
        if term:
            query_params['q'] = term
        if group_id:
            query_params['group'] = group_id

        # TODO find a way to remove this verify = False
        response = requests.get(
            self.contacts_url, headers=headers, params=query_params, verify=False
        )
        if response.status_code != 200:
            return []

        logger.debug('Sucessfully fetched contacts from google')
        logger.debug('Raw data: %s', response.text)
        for contact in response.json().get('feed', {}).get('entry', []):
            yield self.formatter.format(contact)

    def _get_my_contacts_group_id(self, headers):
        query_params = {'alt': 'json'}
        response = requests.get(
            self.groups_url, headers=headers, params=query_params, verify=False
        )
        if response.status_code != 200:
            return

        logger.debug('Fetched groups from Google')
        logger.debug('Raw data: %s', response.text)
        groups = response.json().get('feed', {}).get('entry', [])
        for group in groups:
            if group.get('gContact$systemGroup', {}).get('id') == 'Contacts':
                return group.get('id', {}).get('$t')

    def _paginate(self, contacts, limit=None, offset=None, **_):
        if limit is None and offset is None:
            return contacts

        if offset:
            end = contacts[offset:]
        else:
            end = contacts

        if limit is None:
            return end

        return end[:limit]

    def _sort(self, contacts, order=None, direction=None, **_):
        if not order:
            return contacts

        reverse = direction == 'desc'
        return sorted(contacts, key=itemgetter(order), reverse=reverse)

    def headers(self, google_token):
        return {
            'User-Agent': self.USER_AGENT,
            'Authorization': 'Bearer {}'.format(google_token),
            'Accept': 'application/json',
            'GData-Version': '3.0',
        }


def get_google_access_token(user_uuid, wazo_token, **auth_config):
    try:
        auth = Auth(token=wazo_token, **auth_config)
        return auth.external.get('google', user_uuid).get('access_token')
    except requests.HTTPError as e:
        logger.error('Google token could not be fetched from wazo-auth, error: %s', e)
        raise GoogleTokenNotFoundException(user_uuid)
    except requests.exceptions.ConnectionError as e:
        logger.error(
            'Unable to connect auth-client for the given parameters: %s, error: %s.',
            auth_config,
            e,
        )
        raise GoogleTokenNotFoundException(user_uuid)
    except requests.RequestException as e:
        logger.error('Error occured while connecting to wazo-auth, error: %s', e)


class ContactFormatter:

    chars_to_remove = [' ', '-', '(', ')']

    def format(self, contact):
        return {
            'id': self._extract_id(contact),
            'name': self._extract_name(contact),
            'firstname': self._extract_first_name(contact),
            'numbers_by_label': self._extract_numbers_by_label(contact),
            'numbers': self._extract_numbers(contact),
            'emails': self._extract_emails(contact),
        }

    @classmethod
    def _extract_emails(cls, contact):
        emails = []
        for email in contact.get('gd$email', []):
            address = email.get('address')
            if not address:
                continue
            emails.append(address)
        return emails

    @classmethod
    def _extract_numbers(cls, contact):
        numbers_by_label = cls._extract_numbers_by_label(contact)
        numbers = []
        mobile = None

        for type_, number in numbers_by_label.items():
            if type_ == 'mobile':
                mobile = number
            else:
                numbers.append(number)

        if mobile:
            numbers.append(mobile)

        return numbers

    @staticmethod
    def _extract_id(contact):
        url = contact.get('id', {}).get('$t', '')
        if not url:
            return

        _, id_ = url.rsplit('/', 1)
        return id_

    @classmethod
    def _extract_numbers_by_label(cls, contact):
        numbers = {}
        for number in contact.get('gd$phoneNumber', []):
            type_ = cls._extract_type(number)
            if not type_:
                continue

            number = number.get('$t')
            if not number:
                continue

            for char in cls.chars_to_remove:
                number = number.replace(char, '')

            numbers[type_] = number

        return numbers

    @staticmethod
    def _extract_name(contact):
        return contact.get('title', {}).get('$t', '')

    @classmethod
    def _extract_first_name(cls, contact):
        return contact.get('gd$name', {}).get('gd$givenName', {}).get('$t', '')

    @staticmethod
    def _extract_type(entry):
        rel = entry.get('rel')
        if rel:
            _, type_ = rel.rsplit('#', 1)
        else:
            type_ = entry.get('label')
        return type_
