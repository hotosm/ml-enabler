"""empty message

Revision ID: b08b77c1bb94
Revises: 29c35399c52d
Create Date: 2019-05-21 17:12:12.691355

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'b08b77c1bb94'
down_revision = '29c35399c52d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('predictions', 'predictions')
    op.add_column('predictions', sa.Column('predictions', postgresql.JSONB(), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('predictions', 'predictions')
    op.drop_column('predictions', sa.Column('predictions', postgresql.JSONB(), nullable=False))
    # ### end Alembic commands ###
