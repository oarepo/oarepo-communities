#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Cross-repository ("global") collections built on a designated community.

A single Invenio community — the one whose slug matches
``INVENIO_COLLECTIONS_COMMUNITY_SLUG`` — is treated as a holder for
collection trees that should return records from every community, not only
records tagged with the holder. See
``oarepo_communities/services/community_records/service.py`` for the
records-side behavior and ``views.py`` in this package for the UI.
"""

from __future__ import annotations
