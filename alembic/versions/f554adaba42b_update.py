# noinspection SpellCheckingInspection
"""Update

Revision ID: f554adaba42b
Revises: a96944975680
Create Date: 2021-09-19 20:36:38.087084

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
# noinspection SpellCheckingInspection
revision = 'f554adaba42b'
down_revision = 'a96944975680'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('sensorsdata')
    op.drop_table('alertevent')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # noinspection SpellCheckingInspection
    op.create_table('alertevent',
                    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
                    sa.Column('time_created', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False,
                              nullable=True),
                    sa.Column('owner', sa.VARCHAR(), autoincrement=False, nullable=False),
                    sa.Column('log_level', sa.VARCHAR(), autoincrement=False, nullable=False),
                    sa.Column('description', sa.VARCHAR(), autoincrement=False, nullable=False),
                    sa.PrimaryKeyConstraint('id', name='alertevent_pkey')
                    )
    # noinspection SpellCheckingInspection
    op.create_table('sensorsdata',
                    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
                    sa.Column('time_created', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False,
                              nullable=True),
                    sa.Column('address', sa.INTEGER(), autoincrement=False, nullable=False),
                    sa.Column('current_light_level', sa.INTEGER(), autoincrement=False, nullable=False),
                    sa.PrimaryKeyConstraint('id', name='sensorsdata_pkey')
                    )
    # ### end Alembic commands ###
