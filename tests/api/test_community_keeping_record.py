# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
import pytest

from tests.api.helpers import CommunityEnforcingRecord, make_sample_record


def test_constructor(app, db):
    rec = CommunityEnforcingRecord({})
    assert rec['_primary_community'] == 'A'


def test_schema_create(app, db):
    pid, rec = make_sample_record('no-community', None, None)
    assert rec['_primary_community'] == 'A'

    with pytest.raises(AttributeError):
        make_sample_record('invalid-community', 'C', None)


def test_clear(app, db):
    pid, rec = make_sample_record('clear-community', 'A', None)
    rec.clear()
    assert rec['_primary_community'] == 'A'


def test_update(app, db):
    pid, rec = make_sample_record('update-community', 'A', None)
    with pytest.raises(AttributeError):
        rec.update({'_primary_community': 'B'})

    rec.update({'title': 'blah'})
    assert rec['title'] == 'blah'


def test_set(app, db):
    pid, rec = make_sample_record('set-community', 'A', None)
    with pytest.raises(AttributeError):
        rec['_primary_community'] = 'C'

    # should pass as this is an existing community
    rec['_primary_community'] = 'B'


def test_delete(app, db):
    pid, rec = make_sample_record('delete-community', 'A', None)
    with pytest.raises(AttributeError):
        del rec['_primary_community']


def test_patch(app, db):
    pid, rec = make_sample_record('patch-community', 'A', None)
    with pytest.raises(AttributeError):
        rec.patch([
            {
                'op': 'replace',
                'path': '/_primary_community',
                'value': 'invalid'
            }
        ])

    rec.patch([
        {
            'op': 'replace',
            'path': '/_primary_community',
            'value': 'B'
        }
    ])
