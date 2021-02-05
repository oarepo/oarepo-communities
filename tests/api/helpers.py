# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration.

See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""
import uuid
from collections import namedtuple

from invenio_indexer.api import RecordIndexer
from invenio_pidstore.minters import recid_minter
from invenio_records import Record

from oarepo_communities.record import CommunityKeepingMixin


class CommunityEnforcingRecord(CommunityKeepingMixin, Record):
    """Record that prevents community data to be modified/removed."""


PIDRecord = namedtuple('PIDRecord', 'pid record')


def make_sample_record(db, title, community_id, state='filling'):
    rec = {
        'title': title,
        '_primary_community': community_id,
        'state': state
    }
    record_uuid = uuid.uuid4()
    pid = recid_minter(record_uuid, rec)
    rec = CommunityEnforcingRecord.create(rec, id_=record_uuid)
    db.session.commit()
    indexer = RecordIndexer()
    indexer.index(rec)
    return PIDRecord(pid, rec)
