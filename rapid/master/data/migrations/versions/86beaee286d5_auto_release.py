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

auto_release

Revision ID: 86beaee286d5
Revises: 28fd8ab077e8
Create Date: 2018-06-19 14:40:27.252598

"""

# revision identifiers, used by Alembic.
revision = '86beaee286d5'
down_revision = '28fd8ab077e8'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


def upgrade():
    if 'sqlite' == op.get_context().dialect.name:
        op.add_column('vcs_releases', sa.Column('auto_release', sa.Boolean(), default=False))
    else:
        op.add_column('vcs_releases', sa.Column('auto_release', sa.Boolean(), default=False, nullable=False))


def downgrade():
    op.drop_column('vcs_releases', 'auto_release')
