"""
Copyright (c) 2015 Michael Bright and Bamboo HR LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

vcs_releases

Revision ID: 28fd8ab077e8
Revises: ce9be6e8354c
Create Date: 2018-06-05 18:46:26.844276

"""

# revision identifiers, used by Alembic.
revision = '28fd8ab077e8'
down_revision = 'ce9be6e8354c'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from rapid.lib.constants import VcsReleaseStepType

def upgrade():
    op.create_table('vcs_releases',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('search_filter', sa.String(length=500), nullable=False),
                    sa.Column('notification_id', sa.String(length=250), nullable=False),
                    sa.Column('vcs_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['vcs_id'], ['vcs.id'], ),
                    sa.PrimaryKeyConstraint('id'),
                    mysql_engine='InnoDB'
                    )
    op.create_index(op.f('ix_vcs_releases_id'), 'vcs_releases', ['id'], unique=False)
    op.create_index(op.f('ix_vcs_releases_vcs_id'), 'vcs_releases', ['vcs_id'], unique=False)

    op.create_table('vcs_release_steps',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(length=250), nullable=False),
                    sa.Column('custom_id', sa.String(length=250), nullable=False),
                    sa.Column('user_required', sa.Boolean(), nullable=False),
                    sa.Column('sort_order', sa.Integer(), nullable=True),
                    sa.Column('type', sa.Enum(*list(map(lambda x: x.name, VcsReleaseStepType))), nullable=False),
                    sa.Column('vcs_release_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['vcs_release_id'], ['vcs_releases.id'], ),
                    sa.PrimaryKeyConstraint('id'),
                    mysql_engine='InnoDB'
                    )
    op.create_index(op.f('ix_vcs_release_steps_id'), 'vcs_release_steps', ['id'], unique=False)
    op.create_index(op.f('ix_vcs_release_steps_vcs_release_id'), 'vcs_release_steps', ['vcs_release_id'], unique=False)


def downgrade():
    op.drop_table('vcs_release_steps')
    op.drop_table('vcs_releases')
