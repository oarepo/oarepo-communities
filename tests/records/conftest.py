# Copyright (c) 2022 CESNET
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Pytest configuration.

See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""

import pytest
from invenio_indexer.api import RecordIndexer

from .mock_module.api import MockRecord


@pytest.fixture()
def indexer():
    """Indexer instance with correct Record class."""
    return RecordIndexer(
        record_cls=MockRecord, record_to_index=lambda r: (r.index._name, '_doc')
    )
