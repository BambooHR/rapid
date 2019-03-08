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
# pylint: disable=broad-except
import os
import re
import sys
import hmac
import logging
import datetime

from hashlib import sha1
from rapid.lib.version import Version

logger = logging.getLogger("rapid")


def deep_merge(_a, _b, path=None):
    "merges b into a"
    if path is None:
        path = []
    for key in _b:
        if key in _a:
            if isinstance(_a[key], dict) and isinstance(_b[key], dict):
                deep_merge(_a[key], _b[key], path + [str(key)])
            elif isinstance(_a.get(key, None), list) and isinstance(_b.get(key, None), list):
                _a[key].extend(_b[key])
            elif _a[key] == _b[key]:
                pass  # same leaf value
            else:
                raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
        else:
            if isinstance(_a.get(key, None), list) and isinstance(_b.get(key, None), list):
                _a[key].extend(_b[key])
            else:
                _a[key] = _b[key]
    return _a


class RoutingUtil(object):

    @staticmethod
    def is_valid_request(sent_api_key, api_key):
        return str(sent_api_key) == str(api_key)

    @staticmethod
    def get_cihub_signature(secret_key, data):
        return hmac.new(secret_key.encode('ascii', 'ignore'), data, sha1).hexdigest()


class ORMUtil(object):
    @staticmethod
    def get_filtered_query(query, _filter, clazz):  # pylint: disable=too-many-locals
        if _filter is not None:
            joined_classes = []
            for token in _filter.split(':=:'):
                _m = re.match('(.*)(_eq_|_ne_|_gt_|_lt_|_in_|_ge_|_le_|_like_)(.*)', token)
                if not _m:
                    return query

                group1 = _m.group(1).split('.')
                _op = _m.group(2).replace('_', '')
                value = _m.group(3)

                if len(group1) > 1:
                    final_class = None
                    final_column = None
                    current_class = clazz
                    while len(group1) > 1:

                        nested_attribute = group1[1]
                        column_name = group1.pop(0)

                        attr = getattr(current_class, column_name, None)
                        final_class = attr.property.mapper.class_
                        final_column = getattr(final_class, nested_attribute, None)

                        parent_name = final_column.parent.mapper.class_
                        if parent_name not in joined_classes:
                            query = query.join(final_column.parent.mapper.class_)
                            joined_classes.append(parent_name)

                        current_class = final_column.parent.mapper.class_

                    if final_class is not None and final_column is not None:
                        query = ORMUtil.get_embedded_filter(final_class, final_column.name, _op, value, query)
                else:
                    column_name = group1[0]
                    if hasattr(clazz, column_name):
                        query = ORMUtil.get_column_filter(clazz, column_name, _op, value, query)
                    else:
                        logger.info("Not found: {}".format(_m.group(1)))
        return query

    @staticmethod
    def get_column_filter(clazz, column_name, _op, value, query):
        if hasattr(clazz, column_name):
            query = ORMUtil.get_embedded_filter(clazz, column_name, _op, value, query)
            return query
        raise Exception("Missing attribute")

    @staticmethod
    def get_embedded_filter(clazz, column_name, _op, value, query):
        if hasattr(clazz, column_name):
            column = getattr(clazz, column_name, None)
            filt = None
            if _op == 'in':
                filt = column.in_(value.split(','))
            else:
                attr = None
                try:
                    for _e in ['%s', '%s_', '__%s__']:
                        if hasattr(column, _e % _op):
                            attr = _e % _op
                except Exception as exception:
                    logger.info("\n\n")
                    logger.error(exception)

                if value == 'null':
                    value = None

                if column.type.python_type == bool:
                    value = value == 'True'
                elif column.type.python_type == datetime.datetime:
                    try:
                        value = datetime.datetime.utcfromtimestamp(float(value))  # Python timestamp
                    except ValueError:
                        value = datetime.datetime.utcfromtimestamp(float(value / 1e3))  # Traditional linux timestamp
                filt = getattr(column, attr)(value)
            query = query.filter(filt)
        return query


class UpgradeUtil(object):

    @staticmethod
    def upgrade_version(version, configuration, attempted_reinstall=False):
        if UpgradeUtil._install(version, configuration):
            try:
                import uwsgi
                uwsgi.reload()
            except ImportError:
                import traceback
                traceback.print_exc()
                return False
            return True
        if not attempted_reinstall:
            if UpgradeUtil.upgrade_version(Version.get_version(), configuration, True):
                return False

        raise Exception("Server was unable to upgrade nor restore to previous version!")

    @staticmethod
    def _install(version, configuration):
        version = version.split(';')[0]
        assert re.search(r'[^a-zA-Z\-0-9.]', version) is None, "Invalid Version string."
        
        try:
            logger.info("installing version: {}".format(version))
            return_code = os.system("{}/bin/pip install -i {} {} rapid-framework=={}".format(sys.prefix, configuration.install_uri, configuration.install_options, version))
            return return_code == 0
        except Exception as exception:
            logger.error(exception)
            return False
