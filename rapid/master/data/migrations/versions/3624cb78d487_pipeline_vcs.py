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

pipeline_vcs

Revision ID: 3624cb78d487
Revises: 3d9c6b345dff
Create Date: 2016-02-01 16:37:47.573192

"""

# revision identifiers, used by Alembic.
revision = '3624cb78d487'
down_revision = '3d9c6b345dff'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('vcs', sa.Column('pipeline_id', sa.Integer(), nullable=True))
    if 'sqlite' != op.get_context().dialect.name:
        op.create_index(op.f('ix_vcs_pipeline_id'), 'vcs', ['pipeline_id'], unique=False)
        op.create_foreign_key(None, 'vcs', 'pipelines', ['pipeline_id'], ['id'])
    ### end Alembic commands ###


def downgrade():
    if 'sqlite' != op.get_context().dialect.name:
        op.drop_constraint(None, 'vcs', type_='foreignkey')
        op.drop_index(op.f('ix_vcs_pipeline_id'), table_name='vcs')

    op.drop_column('vcs', 'pipeline_id')
    ### end Alembic commands ###
