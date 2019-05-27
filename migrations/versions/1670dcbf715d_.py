"""empty message

Revision ID: 1670dcbf715d
Revises: b08b77c1bb94
Create Date: 2019-05-23 17:53:18.609850

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1670dcbf715d'
down_revision = 'b08b77c1bb94'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, 'ml_models', ['name'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'ml_models', type_='unique')
    # ### end Alembic commands ###
