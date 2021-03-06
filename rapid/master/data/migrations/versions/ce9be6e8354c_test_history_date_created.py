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

test_history_date_created

Revision ID: ce9be6e8354c
Revises: bf363c3a9ef0
Create Date: 2018-04-30 18:44:54.258839

"""

# revision identifiers, used by Alembic.
import datetime

from sqlalchemy import func

revision = 'ce9be6e8354c'
down_revision = 'bf363c3a9ef0'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    if 'sqlite' == op.get_context().dialect.name:
        op.add_column('qa_test_histories', sa.Column('date_created', sa.DateTime(), default=datetime.datetime.utcnow()))
    else:
        op.add_column('qa_test_histories', sa.Column('date_created', sa.DateTime(), nullable=False, server_default=func.now(), default=datetime.datetime.utcnow()))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('qa_test_histories', 'date_created')
    ### end Alembic commands ###
