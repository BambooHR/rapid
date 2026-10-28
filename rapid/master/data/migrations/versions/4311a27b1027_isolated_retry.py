"""Persist isolated slice retries across worker completion requests."""
from alembic import op
import sqlalchemy as sa

revision = '4311a27b1027'
down_revision = 'cf1a4a9becad'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('stage_instances', sa.Column('suppress_downstream', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('action_instances', sa.Column('isolated_retry', sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade():
    op.drop_column('action_instances', 'isolated_retry')
    op.drop_column('stage_instances', 'suppress_downstream')
