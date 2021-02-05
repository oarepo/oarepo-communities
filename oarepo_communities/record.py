# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
from elasticsearch_dsl import Q
from elasticsearch_dsl.query import Bool
from flask import request
from invenio_records_rest.facets import terms_filter
from oarepo_enrollment_permissions import RecordsSearchMixin


class CommunityRecordMixin():
    """Community keeping record Mixin."""
