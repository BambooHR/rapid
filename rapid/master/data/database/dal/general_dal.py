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


class GeneralDal(object):

    def is_serviceable(self, model):  # pylint: disable=unused-argument
        return True

    def register_url_rules(self, flask_app): # pylint: disable=unused-argument
        pass

    def edit_object(self, session, clazz, _id, in_json):
        instance = session.query(clazz).filter(clazz.id == _id).one()
        self._set_attributes(instance, in_json)
        session.add(instance)
        session.commit()

        return instance

    def delete_object(self, session, clazz, _id):
        instance = session.query(clazz).filter(clazz.id == _id).one()
        session.delete(instance)
        session.commit()

        return instance

    def _set_attributes(self, instance, in_json):
        for key in in_json.keys():
            if hasattr(instance, key):
                setattr(instance, key, in_json[key])

    def get_instance(self, clazz, in_json):
        if in_json:
            return clazz(**in_json)
        return clazz()

    def create_object(self, session, clazz, in_json):
        instance = self.get_instance(clazz, in_json)
        session.add(instance)
        session.commit()
        return instance.serialize()
