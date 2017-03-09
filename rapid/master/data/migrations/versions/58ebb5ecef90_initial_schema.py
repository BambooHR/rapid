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

initial_schema

Revision ID: 58ebb5ecef90
Revises: 
Create Date: 2015-12-09 13:39:15.566607

"""

# revision identifiers, used by Alembic.
from rapid.workflow.data.models import Status

revision = '58ebb5ecef90'
down_revision = None
branch_labels = ('default',)
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('pipelines',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_engine='InnoDB'
    )
    op.create_table('statistics',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_engine='InnoDB'
    )
    op.create_table('statuses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.Column('type', sa.String(length=50), nullable=False),
    sa.Column('display_name', sa.String(length=100), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    mysql_engine='InnoDB'
    )
    op.create_table('pipeline_instances',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_date', sa.DateTime(), nullable=True),
    sa.Column('start_date', sa.DateTime(), nullable=True),
    sa.Column('end_date', sa.DateTime(), nullable=True),
    sa.Column('pipeline_id', sa.Integer(), nullable=False),
    sa.Column('status_id', sa.Integer(), nullable=False),
    sa.Column('priority', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['pipeline_id'], ['pipelines.id'], ),
    sa.ForeignKeyConstraint(['status_id'], ['statuses.id'], ),
    sa.PrimaryKeyConstraint('id'),
    mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_pipeline_instances_priority'), 'pipeline_instances', ['priority'], unique=False)
    op.create_table('stages',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.Column('order', sa.Integer(), nullable=False),
    sa.Column('pipeline_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['pipeline_id'], ['pipelines.id'], ),
    sa.PrimaryKeyConstraint('id'),
    mysql_engine='InnoDB'
    )
    op.create_table('pipeline_parameters',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('pipeline_instance_id', sa.Integer(), nullable=False),
    sa.Column('parameter', sa.String(length=200), nullable=False),
    sa.Column('value', sa.String(length=4000), nullable=False),
    sa.ForeignKeyConstraint(['pipeline_instance_id'], ['pipeline_instances.id'], ),
    sa.PrimaryKeyConstraint('id'),
    mysql_engine='InnoDB'
    )
    op.create_table('pipeline_statistics',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('pipeline_instance_id', sa.Integer(), nullable=False),
    sa.Column('statistics_id', sa.Integer(), nullable=False),
    sa.Column('value', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['pipeline_instance_id'], ['pipeline_instances.id'], ),
    sa.ForeignKeyConstraint(['statistics_id'], ['statistics.id'], ),
    sa.PrimaryKeyConstraint('id'),
    mysql_engine='InnoDB'
    )
    op.create_table('stage_instances',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_date', sa.DateTime(), nullable=True),
    sa.Column('start_date', sa.DateTime(), nullable=True),
    sa.Column('end_date', sa.DateTime(), nullable=True),
    sa.Column('order', sa.Integer(), nullable=False),
    sa.Column('status_id', sa.Integer(), nullable=False),
    sa.Column('pipeline_instance_id', sa.Integer(), nullable=False),
    sa.Column('stage_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['pipeline_instance_id'], ['pipeline_instances.id'], ),
    sa.ForeignKeyConstraint(['stage_id'], ['stages.id'], ),
    sa.ForeignKeyConstraint(['status_id'], ['statuses.id'], ),
    sa.PrimaryKeyConstraint('id'),
    mysql_engine='InnoDB'
    )
    op.create_table('workflows',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.Column('order', sa.Integer(), nullable=False),
    sa.Column('stage_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['stage_id'], ['stages.id'], ),
    sa.PrimaryKeyConstraint('id'),
    mysql_engine='InnoDB'
    )
    op.create_table('actions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('cmd', sa.String(length=255), nullable=False),
    sa.Column('executable', sa.String(length=100), nullable=False),
    sa.Column('args', sa.String(length=255), nullable=False),
    sa.Column('order', sa.Integer(), nullable=False),
    sa.Column('manual', sa.Boolean(), nullable=False),
    sa.Column('grain', sa.String(length=100), nullable=True),
    sa.Column('workflow_id', sa.Integer(), nullable=False),
    sa.Column('pipeline_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['pipeline_id'], ['pipelines.id'], ),
    sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ),
    sa.PrimaryKeyConstraint('id'),
    mysql_engine='InnoDB'
    )
    op.create_table('workflow_instances',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_date', sa.DateTime(), nullable=True),
    sa.Column('start_date', sa.DateTime(), nullable=True),
    sa.Column('end_date', sa.DateTime(), nullable=True),
    sa.Column('order', sa.Integer(), nullable=False),
    sa.Column('status_id', sa.Integer(), nullable=False),
    sa.Column('stage_instance_id', sa.Integer(), nullable=False),
    sa.Column('workflow_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['stage_instance_id'], ['stage_instances.id'], ),
    sa.ForeignKeyConstraint(['status_id'], ['statuses.id'], ),
    sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ),
    sa.PrimaryKeyConstraint('id'),
    mysql_engine='InnoDB'
    )
    op.create_table('action_instances',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_date', sa.DateTime(), nullable=True),
    sa.Column('start_date', sa.DateTime(), nullable=True),
    sa.Column('end_date', sa.DateTime(), nullable=True),
    sa.Column('cmd', sa.String(length=255), nullable=False),
    sa.Column('executable', sa.String(length=100), nullable=False),
    sa.Column('args', sa.String(length=255), nullable=False),
    sa.Column('order', sa.Integer(), nullable=False),
    sa.Column('manual', sa.Boolean(), nullable=False),
    sa.Column('slice', sa.String(length=25), nullable=False),
    sa.Column('grain', sa.String(length=100), nullable=True),
    sa.Column('assigned_to', sa.String(length=75), nullable=True),
    sa.Column('status_id', sa.Integer(), nullable=False),
    sa.Column('action_id', sa.Integer(), nullable=False),
    sa.Column('workflow_instance_id', sa.Integer(), nullable=False),
    sa.Column('pipeline_instance_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['pipeline_instance_id'], ['pipeline_instances.id'], ),
    sa.ForeignKeyConstraint(['action_id'], ['actions.id'], ),
    sa.ForeignKeyConstraint(['status_id'], ['statuses.id'], ),
    sa.ForeignKeyConstraint(['workflow_instance_id'], ['workflow_instances.id'], ),
    sa.PrimaryKeyConstraint('id'),
    mysql_engine='InnoDB'
    )
    ### end Alembic commands ###

    op.bulk_insert(Status.__table__, [
        {"id": 1, "name": "NEW", "display_name": "New", "type": "success", "active": True},
        {"id": 2, "name": "READY", "display_name": "Ready", "type": "success", "active": True},
        {"id": 3, "name": "INPROGRESS", "display_name": "In Progress", "type": "success", "active": True},
        {"id": 4, "name": "SUCCESS", "display_name": "Success", "type": "success", "active": True},
        {"id": 5, "name": "FAILED", "display_name": "Failed", "type": "failed", "active": True},
        {"id": 6, "name": "MERGECONFLICT", "display_name": "Merge Conflict", "type": "failed", "active": True},
        {"id": 7, "name": "UNKOWN", "display_name": "Unknown", "type": "failed", "active": True},
        {"id": 8, "name": "CANCELED", "display_name": "Canceled", "type": "canceled", "active": True},
        {"id": 9, "name": "UNSTABLE", "display_name": "Unstable", "type": "failed", "active": True}
    ])


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('action_instances')
    op.drop_table('workflow_instances')
    op.drop_table('actions')
    op.drop_table('workflows')
    op.drop_table('stage_instances')
    op.drop_table('pipeline_statistics')
    op.drop_table('pipeline_parameters')
    op.drop_table('stages')
    op.drop_index(op.f('ix_pipeline_instances_priority'), table_name='pipeline_instances')
    op.drop_table('pipeline_instances')
    op.drop_table('statuses')
    op.drop_table('statistics')
    op.drop_table('pipelines')
    ### end Alembic commands ###
