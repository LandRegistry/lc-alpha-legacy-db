"""initial lc table

Revision ID: 1cf835bedce
Revises: 
Create Date: 2015-07-10 08:39:17.829823

"""

# revision identifiers, used by Alembic.
revision = '1cf835bedce'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('lc_mock',
                    sa.Column('time', sa.TIMESTAMP(), primary_key=True),
                    sa.Column('registration_no', sa.String(), nullable=False),
                    sa.Column('priority_notice', sa.String(), nullable=False),
                    sa.Column('reverse_name', sa.String(), nullable=False),
                    sa.Column('property_county', sa.SMALLINT(), nullable=False),
                    sa.Column('registration_date', sa.Date(), nullable=False),
                    sa.Column('class_type', sa.String(), nullable=False),
                    sa.Column('remainder_name', sa.VARCHAR(), nullable=False),
                    sa.Column('punctuation_code', sa.VARCHAR(), nullable=False),
                    sa.Column('name', sa.VARCHAR(), nullable=False),
                    sa.Column('address', sa.VARCHAR(), nullable=False),
                    sa.Column('occupation', sa.VARCHAR(), nullable=False),
                    sa.Column('counties', sa.VARCHAR(), nullable=False),
                    sa.Column('amendment_info', sa.VARCHAR(), nullable=False),
                    sa.Column('property', sa.VARCHAR(), nullable=False),
                    sa.Column('parish_district', sa.VARCHAR(), nullable=False),
                    sa.Column('priority_notice_ref', sa.VARCHAR(), nullable=False))
    pass


def downgrade():
    op.drop_table('lc_mock')
    pass
