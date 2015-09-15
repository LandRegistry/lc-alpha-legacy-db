"""Key Holders Legacy Table

Revision ID: 320eb512796
Revises: 1cf835bedce
Create Date: 2015-09-15 07:41:38.580180

"""

# revision identifiers, used by Alembic.
revision = '320eb512796'
down_revision = '1cf835bedce'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    # Partial replication of the table we need from the legacy. Because
    # they're not needed, foreign keys (e.g. group) and related tables are
    # being omitted.
    op.create_table('keyholders',
                    sa.Column('id', sa.Integer(), primary_key=True),  # Inaccurate
                    sa.Column('number', sa.String()),
                    sa.Column('account_code', sa.CHAR()),
                    sa.Column('postcode', sa.String()),
                    sa.Column('name_length_1', sa.Integer()),    # This table is ancient and quite strange!
                    sa.Column('name_length_2', sa.Integer()),
                    sa.Column('address_length_1', sa.Integer()),
                    sa.Column('address_length_2', sa.Integer()),
                    sa.Column('address_length_3', sa.Integer()),
                    sa.Column('address_length_4', sa.Integer()),
                    sa.Column('address_length_5', sa.Integer()),
                    sa.Column('name', sa.String()),
                    sa.Column('address', sa.String())
                    )


def downgrade():
    op.drop_table('keyholders')
