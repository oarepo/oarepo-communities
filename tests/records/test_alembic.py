# Copyright (c) 2022 CESNET
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

import pytest
from invenio_db.utils import drop_alembic_version_table


def test_alembic(base_app, database):
    """Test alembic recipes."""
    db = database
    ext = base_app.extensions['invenio-db']

    if db.engine.name == 'sqlite':
        raise pytest.skip('Upgrades are not supported on SQLite.')

    # Check that this package's SQLAlchemy models have been properly registered
    tables = [x.name for x in db.get_tables_for_bind()]
    assert 'mock_record_metadata' in tables
    assert 'mock_record_community' in tables

    # Drop everything and recreate tables all with Alembic
    db.drop_all()
    drop_alembic_version_table()
    ext.alembic.upgrade()

    # Try to upgrade and downgrade
    ext.alembic.stamp()
    ext.alembic.downgrade(target='96e796392533')
    ext.alembic.upgrade()

    drop_alembic_version_table()
