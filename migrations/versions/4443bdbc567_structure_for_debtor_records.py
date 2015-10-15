"""Structure for debtor records

Revision ID: 4443bdbc567
Revises: 320eb512796
Create Date: 2015-10-15 12:39:09.827193

"""

# revision identifiers, used by Alembic.
revision = '4443bdbc567'
down_revision = '320eb512796'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('debtor_detail',
                    sa.Column('id', sa.TIMESTAMP(), nullable=False, primary_key=True),
                    sa.Column('reg_no', sa.String(), nullable=False),
                    sa.Column('action_type', sa.String(), nullable=False),
                    sa.Column('key_no', sa.String(), nullable=False),
                    sa.Column('session_no', sa.Integer(), nullable=False),
                    sa.Column('year', sa.Integer(), nullable=False),
                    sa.Column('date', sa.String()),
                    sa.Column('status', sa.String()),
                    sa.Column('sequence_no', sa.Integer()),
                    sa.Column('time', sa.String()),
                    sa.Column('gender', sa.String()),
                    sa.Column('debtor_address', sa.String()),
                    sa.Column('debtor_name', sa.String(), nullable=False),
                    sa.Column('occupation', sa.String()),
                    sa.Column('official_receiver', sa.String()),
                    sa.Column('supplementary_info', sa.String()),
                    sa.Column('staff_name', sa.String()))

    op.create_table('previous',
                    sa.Column('prev_date', sa.String(), nullable=False),
                    sa.Column('id', sa.TIMESTAMP(), sa.ForeignKey('debtor_detail.id'), nullable=False),
                    sa.Column('prev_seq_no', sa.Integer(), nullable=False))

    op.create_table('no_hit',
                    sa.Column('date', sa.String(), nullable=False),
                    sa.Column('time', sa.String(), nullable=False),
                    sa.Column('type', sa.String(), nullable=False),
                    sa.Column('complex_number', sa.String()),
                    sa.Column('county', sa.Integer()),
                    sa.Column('sequence', sa.Integer()),
                    sa.Column('gender', sa.String()),
                    sa.Column('title_number', sa.String()),
                    sa.Column('name', sa.String()))

    op.create_table('debtor_control',
                    sa.Column('debtor_id', sa.TIMESTAMP(), primary_key=True, nullable=False),
                    sa.Column('complex_number', sa.String()),
                    sa.Column('county', sa.Integer()),
                    sa.Column('gender', sa.String()),
                    sa.Column('complex_input', sa.String()),
                    sa.Column('address', sa.String()),
                    sa.Column('forename', sa.String()),
                    sa.Column('occupation', sa.String()),
                    sa.Column('surname', sa.String()))

    op.create_table('debtor',
                    sa.Column('id', sa.TIMESTAMP(), sa.ForeignKey('debtor_control.debtor_id'), nullable=False),
                    sa.Column('date', sa.String(), nullable=False),
                    sa.Column('sequence', sa.Integer(), nullable=False))

    op.create_table('debtor_court',
                    sa.Column('reg_date', sa.String(), nullable=False),
                    sa.Column('reg_no', sa.String(), nullable=False),
                    sa.Column('reg_type', sa.String(), nullable=False),
                    sa.Column('key_number', sa.String(), nullable=False),
                    sa.Column('session', sa.Integer(), nullable=False),
                    sa.Column('year', sa.Integer(), nullable=False),
                    sa.Column('debtor_id', sa.TIMESTAMP(), sa.ForeignKey('debtor_control.debtor_id'), nullable=False),
                    sa.Column('supplementary_info', sa.String()))

    op.create_table('property_detail',
                    sa.Column('id', sa.TIMESTAMP(), sa.ForeignKey('debtor_detail.id'), primary_key=True, nullable=False),
                    sa.Column('sequence', sa.Integer(), primary_key=True, nullable=False),
                    sa.Column('status', sa.String(), nullable=False),
                    sa.Column('prop_status', sa.String()),
                    sa.Column('title_message', sa.String()),
                    sa.Column('associated_ref', sa.String()),
                    sa.Column('title_number', sa.String(), nullable=False),
                    sa.Column('description', sa.String()),
                    sa.Column('address', sa.String()),
                    sa.Column('name', sa.String(), nullable=False))


def downgrade():
    op.drop_table('property_detail')
    op.drop_table('debtor_court')
    op.drop_table('debtor')
    op.drop_table('debtor_control')
    op.drop_table('no_hit')
    op.drop_table('previous')
    op.drop_table('debtor_detail')
