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

app_configuration

Revision ID: 9327e407fdfd
Revises: 8d5f3b5854d0
Create Date: 2020-11-16 11:31:47.643156

"""

# revision identifiers, used by Alembic.
from rapid.workflow.data.models import AppConfiguration

revision = '9327e407fdfd'
down_revision = '8d5f3b5854d0'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('app_configurations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('process_queue', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_app_configurations_id'), 'app_configurations', ['id'], unique=False)
    op.bulk_insert(AppConfiguration.__table__, [
        {'id': 1, 'process_queue': True}
    ])


def downgrade():
    op.drop_index(op.f('ix_app_configurations_id'), table_name='app_configurations')
    op.drop_table('app_configurations')
