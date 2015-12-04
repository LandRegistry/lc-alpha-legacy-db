"""Legacy history and document index

Revision ID: 4f745fb35a9
Revises: 23af5578ba
Create Date: 2015-12-04 11:59:54.970684

"""

# revision identifiers, used by Alembic.
revision = '4f745fb35a9'
down_revision = '23af5578ba'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('history',
                    sa.Column('class', sa.String()),
                    sa.Column('number', sa.String()),
                    sa.Column('date', sa.String()),
                    sa.Column('timestamp', sa.TIMESTAMP()),
                    sa.Column('template', sa.String()),
                    sa.Column('text', sa.String()))

    op.create_table('documents',
                    sa.Column('class', sa.String()),
                    sa.Column('number', sa.String()),
                    sa.Column('date', sa.String()),
                    sa.Column('orig_class', sa.String()),
                    sa.Column('orig_number', sa.String()),
                    sa.Column('orig_date', sa.String()),
                    sa.Column('canc_ind', sa.String()),
                    sa.Column('type', sa.String()),
                    sa.Column('timestamp', sa.TIMESTAMP()))


def downgrade():
    op.drop_table('history')
    op.drop_table('documents')
