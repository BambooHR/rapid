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
import datetime
from sqlalchemy import Column, DateTime
# pylint: disable=no-member,too-few-public-methods


class DateModel(object):
    created_date = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    start_date = Column(DateTime, index=True)
    end_date = Column(DateTime, index=True)
