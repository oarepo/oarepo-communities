# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
from invenio_search import RecordsSearch as InvenioRecordsSearch


def test_has_records(app, client, sample_records):
    data = InvenioRecordsSearch(index='records-record-v1.0.0').execute()
    assert data['hits']['total']['value'] > 0


def test_rest_list_primary(client, es, sample_records):
    resp = client.get('https://localhost/A/')
    assert resp.status_code == 200
    assert resp.json['hits']['total'] == 3  # 1 published record in community A
    assert 'B' not in [r['metadata']['_primary_community'] for r in resp.json['hits']['hits']]

    resp = client.get('https://localhost/B/')
    assert resp.status_code == 200
    assert resp.json['hits']['total'] == 8  # 1 published record in community B
    assert 'A' not in [r['metadata']['_primary_community'] for r in resp.json['hits']['hits']]


def test_rest_list_secondary(client, es, sample_records):
    resp = client.get('https://localhost/C/')
    assert resp.status_code == 200
    assert resp.json['hits']['total'] == 1  # 1 published record having secondary community C assigned
    assert resp.json['hits']['hits'][0]['metadata']['_primary_community'] == 'B'
