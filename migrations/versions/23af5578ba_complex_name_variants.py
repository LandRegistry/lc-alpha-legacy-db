"""Complex Name Variants

Revision ID: 23af5578ba
Revises: 4443bdbc567
Create Date: 2015-11-02 13:39:37.491752

"""

# revision identifiers, used by Alembic.
revision = '23af5578ba'
down_revision = '4443bdbc567'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('name_variants',
                    sa.Column('amended_code', sa.CHAR()),
                    sa.Column('amended_date', sa.String()),
                    sa.Column('number', sa.String()),
                    sa.Column('source', sa.String()),
                    sa.Column('user', sa.String()),
                    sa.Column('name', sa.String()))


def downgrade():
    op.drop_table('name_variants')
