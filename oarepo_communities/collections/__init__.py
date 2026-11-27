# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Cross-repository ("global") collections built on a designated community.

A single Invenio community — the one whose slug matches
``COLLECTIONS_COMMUNITY_SLUG`` (expected to be ``"global"``) — is treated as a holder for
collection trees that should return records from every community, not only
records tagged with the holder. The records-side behavior (skipping the
community filter for this community) lives in ``services.py``; see
``views.py`` in this package for the UI.
"""

from __future__ import annotations
