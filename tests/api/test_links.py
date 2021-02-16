# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""


def test_links_from_search(app, client, es, sample_records):
    resp = client.get('https://localhost/C/records-anonymous/')
    assert resp.status_code == 200
    assert resp.json['hits']['total'] == 1  # 1 published record having secondary community C assigned
    assert resp.json['hits']['hits'][0]['links']['self'] == 'https://localhost/B/records-anonymous/6'


def test_links_from_get(app, client, es, sample_records):
    resp = client.get('https://localhost/C/records-anonymous/6')
    assert resp.status_code == 200
    assert resp.json['links']['self'] == 'https://localhost/B/records-anonymous/6'
