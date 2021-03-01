# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
import pytest

from tests.api.helpers import make_sample_record


def test_schema_create(app, db):
    pid, rec = make_sample_record(db, 'no-community', 'A', None)
    assert rec['_primary_community'] == 'A'

    with pytest.raises(AttributeError):
        make_sample_record(db, 'invalid-community', None, None)


def test_primary_community(app, db):
    pid, rec = make_sample_record(db, 'primary', 'A', None)
    assert rec.primary_community == 'A'


def test_secondary_communities(app, db):
    pid, rec = make_sample_record(db, 'secondary', 'A', None, ['B', 'C'])
    assert rec.secondary_communities == ['B', 'C']


def test_clear(app, db):
    pid, rec = make_sample_record(db, 'clear-community', 'A', None)
    rec.clear()
    assert rec['_primary_community'] == 'A'


def test_update(app, db):
    pid, rec = make_sample_record(db, 'update-community', 'A', None)
    with pytest.raises(AttributeError):
        rec.update({'_primary_community': 'B'})

    rec.update({'title': 'blah'})
    assert rec['title'] == 'blah'


def test_set(app, db):
    pid, rec = make_sample_record(db, 'set-community', 'A', None)
    with pytest.raises(AttributeError):
        rec['_primary_community'] = 'C'


def test_delete(app, db):
    pid, rec = make_sample_record(db, 'delete-community', 'A', None)
    with pytest.raises(AttributeError):
        del rec['_primary_community']


def test_patch(app, db):
    pid, rec = make_sample_record(db, 'patch-community', 'A', None)
    with pytest.raises(AttributeError):
        rec.patch([
            {
                'op': 'replace',
                'path': '/_primary_community',
                'value': 'invalid'
            }
        ])
