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

import calendar
import re
from datetime import datetime

from .... import db
from sqlalchemy.ext.declarative import declared_attr, declarative_base

import logging
logger = logging.getLogger("rapid")


class BaseModel(object):

    @declared_attr
    def __tablename__(cls):
        name = "_".join(re.findall('[A-Z]{1}[a-z]*', cls.__name__))
        name = name.lower()
        if name.endswith('s') and re.search("[aeiou]s$", name):
            name = "{}es".format(name)
        elif name.endswith('y'):
            name = name[:-1] + "ies"
        elif not name.endswith('s'):
            name = "%s%s" % (name, "s"[2 == 1:])
        return name

    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = db.Column(db.Integer, primary_key=True, index=True)

    def __repr__(self):
        return "<Model {}>".format(self.__class__)

    def __relationships__(self, reverse=False):
        """
        Return a list of relationships name which are not as a backref
        name in model
        """
        from sqlalchemy.inspection import inspect
        relationships = []
        for item in inspect(self.__class__).relationships:
            relationships.append("{}".format(item).split('.')[1])
        return relationships

    def serialize(self, allowed_children=None, previous_relationship=None):
        serialized = Odict()
        relationships = self.__relationships__()
        fields = [x for x in dir(self) if not x.startswith('_') and x != 'metadata']
        if len(fields) > 1:
            self._serialize_fields(serialized, fields[:len(fields)/2], previous_relationship, allowed_children, relationships)
            self._serialize_fields(serialized, fields[len(fields)/2:], previous_relationship, allowed_children, relationships)
        else:
            self._serialize_fields(serialized, fields, previous_relationship, allowed_children, relationships)
        return serialized

    def _serialize_fields(self, serialized, fields, previous_relationship, allowed_children, relationships):
        for field in fields:
            key_filter = self.__tablename__ if previous_relationship is None else previous_relationship
            allowed_filter = dict(allowed_children) if allowed_children else {}
            if field == 'serialize' \
                    or field == 'query' \
                    or field == 'query_class' \
                    or field == 'convert_to_instance' \
                    or field in relationships:
                if allowed_children and field in relationships:
                    allowed_filter = self.__allowed_iteration(allowed_children, key_filter, field)
                    if field not in allowed_filter:
                        if 'fields' in allowed_filter and field in allowed_filter['fields']:
                            pass
                        else:
                            continue
                else:
                    continue
            value = self.__getattribute__(field)

            if isinstance(value, list):
                value = [item.serialize(allowed_filter, previous_relationship=field) for item in value]
            elif isinstance(value, datetime):
                value = int(calendar.timegm(value.utctimetuple()))
            elif hasattr(value, 'serialize'):
                value = value.serialize(allowed_filter, previous_relationship=field)

            serialized[field] = value
            setattr(serialized, field, value)


    def __allowed_iteration(self, allowed_children, key_filter, field):
        allowed_combine = {}
        if key_filter in allowed_children and field in allowed_children[key_filter]:
            allowed_combine.update({key_filter: allowed_children[key_filter]})
            allowed_combine.update({"fields": allowed_children[key_filter]})

            if field in allowed_children:
                allowed_combine.update({field: allowed_children[field]})
                for field2 in allowed_children[field]:
                    allowed_combine.update(self.__allowed_iteration(allowed_children, field, field2))
        return allowed_combine
    # {pipeline_instances:['stage_instances'], stage_instances: ['workflow_instances'], 'workflow_instances': ['action_instances']

class Odict(dict):
    pass