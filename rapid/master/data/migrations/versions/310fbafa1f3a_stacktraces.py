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

stacktraces

Revision ID: 310fbafa1f3a
Revises: 30b4676b2f86
Create Date: 2016-01-27 09:03:49.746463

"""

# revision identifiers, used by Alembic.
revision = '310fbafa1f3a'
down_revision = '30b4676b2f86'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('stacktraces',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('qa_test_history_id', sa.Integer(), nullable=False),
                    sa.Column('stacktrace', sa.Text(), nullable=True),
                    sa.ForeignKeyConstraint(['qa_test_history_id'], ['qa_test_histories.id'], ),
                    sa.PrimaryKeyConstraint('id'),
                    mysql_engine='InnoDB'
                    )
    op.create_index(op.f('ix_stacktraces_id'), 'stacktraces', ['id'], unique=False)
    op.create_index(op.f('ix_stacktraces_qa_test_history_id'), 'stacktraces', ['qa_test_history_id'], unique=True)
    ### end Alembic commands ###


def downgrade():
    op.drop_index(op.f('ix_stacktraces_qa_test_history_id'), table_name='stacktraces')
    op.drop_index(op.f('ix_stacktraces_id'), table_name='stacktraces')
    op.drop_table('stacktraces')
    ### end Alembic commands ###