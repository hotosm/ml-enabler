"""empty message

Revision ID: 0e3cff90d380
Revises: 65b0dbc13dcb
Create Date: 2020-07-09 10:06:48.224878

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0e3cff90d380'
down_revision = '65b0dbc13dcb'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('predictions', sa.Column('inf_supertile', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    op.drop_column('predictions', 'inf_supertile')
    # ### end Alembic commands ###
