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

adding more indexes

Revision ID: 3781a8185e42
Revises: e2a50a08334a
Create Date: 2016-08-03 03:42:10.327332

"""

# revision identifiers, used by Alembic.
revision = '3781a8185e42'
down_revision = 'e2a50a08334a'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    # ActionInstances
    op.create_index(op.f('ix_action_instances_created_date'), 'action_instances', ['created_date'], unique=False)
    op.create_index(op.f('ix_action_instances_start_date'), 'action_instances', ['start_date'], unique=False)
    op.create_index(op.f('ix_action_instances_end_date'), 'action_instances', ['end_date'], unique=False)

    # PipelineInstances
    op.create_index(op.f('ix_pipeline_instances_created_date'), 'pipeline_instances', ['created_date'], unique=False)
    op.create_index(op.f('ix_pipeline_instances_start_date'), 'pipeline_instances', ['start_date'], unique=False)
    op.create_index(op.f('ix_pipeline_instances_end_date'), 'pipeline_instances', ['end_date'], unique=False)

    # Releases
    op.create_index(op.f('ix_releases_date_created'), 'releases', ['date_created'], unique=False)
    ### end Alembic commands ###


def downgrade():
    # ActionInstances
    op.drop_index(op.f('ix_action_instances_created_date'), table_name='action_instances')
    op.drop_index(op.f('ix_action_instances_start_date'), table_name='action_instances')
    op.drop_index(op.f('ix_action_instances_end_date'), table_name='action_instances')

    # PipelineInstances
    op.drop_index(op.f('ix_pipeline_instances_created_date'), table_name='pipeline_instances')
    op.drop_index(op.f('ix_pipeline_instances_start_date'), table_name='pipeline_instances')
    op.drop_index(op.f('ix_pipeline_instances_end_date'), table_name='pipeline_instances')

    # Releases
    op.drop_index(op.f('ix_releases_date_created'), table_name='releases')

