"""Update

Revision ID: 6891836982aa
Revises: 7581d141d67b
Create Date: 2021-09-19 16:10:55.563421

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = '6891836982aa'
down_revision = '7581d141d67b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_lampsdata_id', table_name='lampsdata')
    op.drop_table('lampsdata')
    op.drop_table('sensorsdata')
    op.drop_table('alertevent')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('alertevent',
                    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
                    sa.Column('time_created', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False,
                              nullable=True),
                    sa.Column('owner', sa.VARCHAR(), autoincrement=False, nullable=False),
                    sa.Column('log_level', sa.VARCHAR(), autoincrement=False, nullable=False),
                    sa.Column('description', sa.VARCHAR(), autoincrement=False, nullable=False),
                    sa.PrimaryKeyConstraint('id', name='alertevent_pkey')
                    )
    op.create_table('sensorsdata',
                    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
                    sa.Column('time_created', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False,
                              nullable=True),
                    sa.Column('address', sa.INTEGER(), autoincrement=False, nullable=False),
                    sa.Column('current_light_level', sa.INTEGER(), autoincrement=False, nullable=False),
                    sa.PrimaryKeyConstraint('id', name='sensorsdata_pkey')
                    )
    op.create_table('lampsdata',
                    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
                    sa.Column('time_created', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False,
                              nullable=True),
                    sa.Column('address', sa.INTEGER(), autoincrement=False, nullable=False),
                    sa.Column('light_tx', postgresql.ARRAY(sa.INTEGER()), autoincrement=False, nullable=False),
                    sa.Column('light_rx', postgresql.ARRAY(sa.INTEGER()), autoincrement=False, nullable=False),
                    sa.Column('volt', postgresql.ARRAY(sa.INTEGER()), autoincrement=False, nullable=False),
                    sa.Column('temp', postgresql.ARRAY(sa.INTEGER()), autoincrement=False, nullable=False),
                    sa.Column('fails', postgresql.ARRAY(sa.INTEGER()), autoincrement=False, nullable=False),
                    sa.Column('max_i', postgresql.ARRAY(sa.INTEGER()), autoincrement=False, nullable=False),
                    sa.Column('blink_rw', postgresql.ARRAY(sa.INTEGER()), autoincrement=False, nullable=False),
                    sa.Column('temp_max', sa.INTEGER(), autoincrement=False, nullable=False),
                    sa.Column('rf_net', sa.INTEGER(), autoincrement=False, nullable=False),
                    sa.Column('group_membership', sa.INTEGER(), autoincrement=False, nullable=False),
                    sa.PrimaryKeyConstraint('id', name='lampsdata_pkey')
                    )
    op.create_index('ix_lampsdata_id', 'lampsdata', ['id'], unique=False)
    # ### end Alembic commands ###
