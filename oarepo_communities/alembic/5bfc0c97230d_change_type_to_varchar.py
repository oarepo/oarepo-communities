#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Change type to varchar."""

from alembic import op

# revision identifiers, used by Alembic.
revision = '5bfc0c97230d'
down_revision = 'd6ae7ea25cdb'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute('ALTER TABLE oarepo_communities ALTER COLUMN "type" TYPE varchar(16) USING "type"::varchar')
    # ### end Alembic commands ###


def downgrade():
    """Downgrade database."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute('ALTER TABLE oarepo_communities ALTER COLUMN "type" TYPE char(16) USING "type"::varchar')
    # ### end Alembic commands ###
