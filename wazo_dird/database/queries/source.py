# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from sqlalchemy import (
    and_,
    exc,
)
from wazo_dird.exception import (
    DuplicatedSourceException,
    NoSuchSource,
)
from .base import BaseDAO
from ..import Source


class SourceCRUD(BaseDAO):

    _UNIQUE_CONSTRAINT_CODE = '23505'

    def count(self, visible_tenants, **list_params):
        filter_ = self._list_filter(visible_tenants, **list_params)
        with self.new_session() as s:
            return s.query(Source).filter(filter_).count()

    def list_(self, visible_tenants, **list_params):
        filter_ = self._list_filter(visible_tenants, **list_params)
        with self.new_session() as s:
            query = s.query(Source).filter(filter_)
            query = self._paginate(query, **list_params)
            return [self._from_db_format(row) for row in query.all()]

    def create(self, source_body):
        with self.new_session() as s:
            self._create_tenant(s, source_body['tenant_uuid'])
            source = self._to_db_format(**source_body)
            s.add(source)
            try:
                s.flush()
            except exc.IntegrityError as e:
                if e.orig.pgcode == self._UNIQUE_CONSTRAINT_CODE:
                    raise DuplicatedSourceException(source_body['name'])
                raise

            return self._from_db_format(source)

    def delete(self, source_uuid, visible_tenants):
        filter_ = self._multi_tenant_filter(source_uuid, visible_tenants)
        with self.new_session() as s:
            nb_deleted = s.query(Source).filter(filter_).delete(synchronize_session=False)

        if not nb_deleted:
            raise NoSuchSource(source_uuid)

    def edit(self, source_uuid, visible_tenants, body):
        filter_ = self._multi_tenant_filter(source_uuid, visible_tenants)
        with self.new_session() as s:
            source = s.query(Source).filter(filter_).first()

            if not source:
                raise NoSuchSource(source_uuid)

            self._update_to_db_format(source, **body)
            try:
                s.flush()
            except exc.IntegrityError as e:
                if e.orig.pgcode == self._UNIQUE_CONSTRAINT_CODE:
                    raise DuplicatedSourceException(body['name'])
                raise

    def get(self, source_uuid, visible_tenants):
        filter_ = self._multi_tenant_filter(source_uuid, visible_tenants)
        with self.new_session() as s:
            source = s.query(Source).filter(filter_).first()

            if not source:
                raise NoSuchSource(source_uuid)

            return self._from_db_format(source)

    def _list_filter(self, visible_tenants, uuid=None, name=None, search=None, **list_params):
        filter_ = Source.tenant_uuid.in_(visible_tenants)
        if uuid is not None:
            filter_ = and_(filter_, Source.uuid == uuid)
        if name is not None:
            filter_ = and_(filter_, Source.name == name)
        if search is not None:
            pattern = '%{}%'.format(search)
            filter_ = and_(filter_, Source.name.ilike(pattern))

        return filter_

    def _multi_tenant_filter(self, source_uuid, visible_tenants):
        return and_(
            Source.tenant_uuid.in_(visible_tenants),
            Source.uuid == source_uuid,
        )

    def _paginate(self, query, limit=None, offset=None, order=None, direction=None, **ignored):
        if order and direction:
            field = None
            if order == 'name':
                field = Source.name

            if field:
                order_clause = field.asc() if direction == 'asc' else field.desc()
                query = query.order_by(order_clause)

        if limit is not None:
            query = query.limit(limit)

        if offset is not None:
            query = query.offset(offset)

        return query

    def _to_db_format(self, tenant_uuid, *args, **kwargs):
        source = Source(tenant_uuid=tenant_uuid)
        return self._update_to_db_format(source, *args, **kwargs)

    @staticmethod
    def _update_to_db_format(
            source,
            name,
            searched_columns,
            first_matched_columns,
            format_columns,
            **extra_fields
    ):
        source.name = name
        source.searched_columns = searched_columns
        source.first_matched_columns = first_matched_columns
        source.format_columns = format_columns
        source.extra_fields = extra_fields
        return source

    @staticmethod
    def _from_db_format(source):
        return dict(
            uuid=source.uuid,
            name=source.name,
            tenant_uuid=source.tenant_uuid,
            searched_columns=source.searched_columns,
            first_matched_columns=source.first_matched_columns,
            format_columns=source.format_columns,
            **source.extra_fields
        )