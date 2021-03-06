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

status_summary

Revision ID: a08ae00f2ba7
Revises: e16dacfc467e
Create Date: 2016-02-03 17:56:13.138231

"""

# revision identifiers, used by Alembic.
revision = 'a08ae00f2ba7'
down_revision = 'e16dacfc467e'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('qa_status_summaries',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('action_instance_id', sa.Integer(), nullable=False),
    sa.Column('status_id', sa.Integer(), nullable=False),
    sa.Column('count', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['action_instance_id'], ['action_instances.id'], ),
    sa.ForeignKeyConstraint(['status_id'], ['statuses.id'], ),
    sa.PrimaryKeyConstraint('id'),
    mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_qa_status_summaries_action_instance_id'), 'qa_status_summaries', ['action_instance_id'], unique=False)
    op.create_index(op.f('ix_qa_status_summaries_id'), 'qa_status_summaries', ['id'], unique=False)
    op.create_index(op.f('ix_qa_status_summaries_status_id'), 'qa_status_summaries', ['status_id'], unique=False)
    op.create_index(op.f('ix_commit_parameters_commit_id'), 'commit_parameters', ['commit_id'], unique=False)
    op.create_index(op.f('ix_commit_parameters_id'), 'commit_parameters', ['id'], unique=False)
    op.create_index(op.f('ix_commit_parameters_name'), 'commit_parameters', ['name'], unique=False)
    op.drop_index('ix_commit_param_commit_id', table_name='commit_parameters')
    op.drop_index('ix_commit_param_id', table_name='commit_parameters')
    op.drop_index('ix_commit_param_name', table_name='commit_parameters')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_index('ix_commit_param_name', 'commit_parameters', ['name'], unique=False)
    op.create_index('ix_commit_param_id', 'commit_parameters', ['id'], unique=False)
    op.create_index('ix_commit_param_commit_id', 'commit_parameters', ['commit_id'], unique=False)
    op.drop_index(op.f('ix_commit_parameters_name'), table_name='commit_parameters')
    op.drop_index(op.f('ix_commit_parameters_id'), table_name='commit_parameters')
    op.drop_index(op.f('ix_commit_parameters_commit_id'), table_name='commit_parameters')
    op.drop_index(op.f('ix_qa_status_summaries_status_id'), table_name='qa_status_summaries')
    op.drop_index(op.f('ix_qa_status_summaries_id'), table_name='qa_status_summaries')
    op.drop_index(op.f('ix_qa_status_summaries_action_instance_id'), table_name='qa_status_summaries')
    op.drop_table('qa_status_summaries')
    ### end Alembic commands ###
