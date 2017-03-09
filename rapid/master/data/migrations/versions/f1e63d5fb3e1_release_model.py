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

release model

Revision ID: f1e63d5fb3e1
Revises: a08ae00f2ba7
Create Date: 2016-03-01 10:15:03.689086

"""

# revision identifiers, used by Alembic.
revision = 'f1e63d5fb3e1'
down_revision = 'a08ae00f2ba7'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=150), nullable=False),
    sa.Column('username', sa.String(length=150), nullable=False, index=True),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_table('releases',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('date_created', sa.DateTime(), nullable=False),
    sa.Column('status_id', sa.Integer(), nullable=False),
    sa.Column('commit_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['commit_id'], ['commits.id'], ),
    sa.ForeignKeyConstraint(['status_id'], ['statuses.id'], ),
    sa.PrimaryKeyConstraint('id'),
    mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_releases_commit_id'), 'releases', ['commit_id'], unique=False)
    op.create_index(op.f('ix_releases_id'), 'releases', ['id'], unique=False)
    op.create_index(op.f('ix_releases_name'), 'releases', ['name'], unique=False)
    op.create_index(op.f('ix_releases_status_id'), 'releases', ['status_id'], unique=False)
    op.create_table('steps',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('custom_id', sa.String(length=25), nullable=False),
    sa.Column('status_id', sa.Integer(), nullable=False),
    sa.Column('user_required', sa.Boolean(), nullable=False),
    sa.Column('release_id', sa.Integer(), nullable=False),
    sa.Column('sort_order', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['release_id'], ['releases.id'], ),
    sa.ForeignKeyConstraint(['status_id'], ['statuses.id'], ),
    sa.PrimaryKeyConstraint('id'),
    mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_steps_id'), 'steps', ['id'], unique=False)
    op.create_index(op.f('ix_steps_release_id'), 'steps', ['release_id'], unique=False)
    op.create_index(op.f('ix_steps_status_id'), 'steps', ['status_id'], unique=False)
    op.create_table('step_users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('step_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('date_created', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['step_id'], ['steps.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_step_users_id'), 'step_users', ['id'], unique=False)
    op.create_index(op.f('ix_step_users_step_id'), 'step_users', ['step_id'], unique=False)
    op.create_index(op.f('ix_step_users_user_id'), 'step_users', ['user_id'], unique=False)
    op.create_table('step_user_comments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('step_user_id', sa.Integer(), nullable=False),
    sa.Column('comment', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['step_user_id'], ['step_users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_step_user_comments_id'), 'step_user_comments', ['id'], unique=False)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_step_user_comments_id'), table_name='step_user_comments')
    op.drop_table('step_user_comments')
    op.drop_index(op.f('ix_step_users_user_id'), table_name='step_users')
    op.drop_index(op.f('ix_step_users_step_id'), table_name='step_users')
    op.drop_index(op.f('ix_step_users_id'), table_name='step_users')
    op.drop_table('step_users')
    op.drop_index(op.f('ix_steps_status_id'), table_name='steps')
    op.drop_index(op.f('ix_steps_release_id'), table_name='steps')
    op.drop_index(op.f('ix_steps_id'), table_name='steps')
    op.drop_table('steps')
    op.drop_index(op.f('ix_releases_status_id'), table_name='releases')
    op.drop_index(op.f('ix_releases_name'), table_name='releases')
    op.drop_index(op.f('ix_releases_id'), table_name='releases')
    op.drop_index(op.f('ix_releases_commit_id'), table_name='releases')
    op.drop_table('releases')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
    ### end Alembic commands ###
