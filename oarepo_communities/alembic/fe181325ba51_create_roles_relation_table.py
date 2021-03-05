#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create roles relation table."""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fe181325ba51'
down_revision = '5bfc0c97230d'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('oarepo_communities_role',
    sa.Column('community_id', sa.String(length=63), nullable=True),
    sa.Column('role_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['community_id'], ['oarepo_communities.id'], name='fk_oarepo_communities_role_community_id'),
    sa.ForeignKeyConstraint(['role_id'], ['accounts_role.id'], name='fk_oarepo_communities_role_role_id'),
    sa.UniqueConstraint('role_id', name=op.f('uq_oarepo_communities_role_role_id'))
    )
    # ### end Alembic commands ###


def downgrade():
    """Downgrade database."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('oarepo_communities_role')
    # ### end Alembic commands ###
