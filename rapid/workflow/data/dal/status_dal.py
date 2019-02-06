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
"""

from rapid.lib import get_db_session
from rapid.master.data.database.dal.general_dal import GeneralDal
from rapid.workflow.data.models import Status


class StatusDal(GeneralDal):

    def __init__(self, db_session=None):
        self.session = db_session

    def get_status_by_id(self, _id):
        if self.session:
            return self.session.query(Status).get(_id).serialize()
        for session in get_db_session():
            return session.query(Status).get(_id).serialize()
