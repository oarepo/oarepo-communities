# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
import uuid
from collections import namedtuple

import flask
from flask import current_app, url_for
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.minters import recid_minter
from invenio_records import Record
from oarepo_enrollment_permissions import create_permission_factory, delete_permission_factory, \
    update_permission_factory, read_permission_factory
from werkzeug.local import LocalProxy

from oarepo_communities.api import OARepoCommunity
from oarepo_communities.links import record_collection_links_factory
from oarepo_communities.record import CommunityKeepingMixin

_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


class TestRecord(CommunityKeepingMixin, Record):
    blueprint = 'tests.api/recid_item'

    @property
    def canonical_url(self):
        return url_for(f'invenio_records_rest.{self.blueprint}',
                       pid_value=self['id'], _external=True)


class LiteEntryPoint:
    def __init__(self, name, val):
        self.name = name
        self.val = val

    def load(self):
        return self.val


def gen_rest_endpoint(pid_type, search_class, record_class, path, custom_read_permission_factory=None):
    return dict(
        pid_type=pid_type,
        pid_minter=pid_type,
        pid_fetcher=pid_type,
        search_class=search_class,
        indexer_class=RecordIndexer,
        links_factory_imp=record_collection_links_factory,
        search_index='records-record-v1.0.0',
        search_type='_doc',
        record_class=record_class,
        record_serializers={
            'application/json': ('invenio_records_rest.serializers'

                                 ':json_v1_response'),
        },
        search_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_search'),
        },
        list_route=f'/{path}/',
        item_route=f'/{path}/<pid({pid_type},record_class="{record_class}"):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        error_handlers=dict(),
        create_permission_factory_imp=create_permission_factory,
        delete_permission_factory_imp=delete_permission_factory,
        update_permission_factory_imp=update_permission_factory,
        read_permission_factory_imp=custom_read_permission_factory or read_permission_factory,
    )


def create_test_role(role, **kwargs):
    """Create a role in the datastore.

    Accesses the application's datastore. An error is thrown if called from
    outside of an application context.

    Returns the created user model object instance, with the plaintext password
    as `user.password_plaintext`.

    :param name: The name of the role.
    :returns: A :class:`invenio_accounts.models.Role` instance.
    """
    assert flask.current_app.testing
    role = _datastore.create_role(name=role, **kwargs)
    _datastore.commit()
    return role


PIDRecord = namedtuple('PIDRecord', 'pid record')


def make_sample_record(db, title, community_id, state='filling', secondary=None):
    rec = {
        'title': title,
        '_primary_community': community_id,
        'state': state,
        '_communities': secondary
    }
    record_uuid = uuid.uuid4()
    pid = recid_minter(record_uuid, rec)
    rec = TestRecord.create(rec, id_=record_uuid)
    db.session.commit()
    indexer = RecordIndexer()
    indexer.index(rec)
    return PIDRecord(pid, rec)


def make_sample_community(db, comid):
    community = OARepoCommunity.create(
        {'title': f'{comid} Title',
         'description': f'Community {comid} description'},
        uuid.uuid4(), uuid.uuid4(), uuid.uuid4,
        id_=comid)
    db.session.commit()
    return community
