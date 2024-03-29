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

release_details

Revision ID: cf1a4a9becad
Revises: 9327e407fdfd
Create Date: 2021-11-08 13:39:35.169197

"""

# revision identifiers, used by Alembic.
revision = 'cf1a4a9becad'
down_revision = '9327e407fdfd'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('release_details',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('release_id', sa.Integer(), nullable=False),
    sa.Column('details', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['release_id'], ['releases.id'], ),
    sa.PrimaryKeyConstraint('id'),
    mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_release_details_id'), 'release_details', ['id'], unique=False)
    op.create_index(op.f('ix_release_details_release_id'), 'release_details', ['release_id'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_release_details_release_id'), table_name='release_details')
    op.drop_index(op.f('ix_release_details_id'), table_name='release_details')
    op.drop_table('release_details')
    # ### end Alembic commands ###
