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

def execute_db_query(query, bind_params=None):
    bind_params = {} if not bind_params else bind_params

    from rapid.lib import get_db_session
    from sqlalchemy.sql import text, bindparam
    t = text(query)
    t.bindparams(*[bindparam(key, expanding=True) for key, value in bind_params.items()])
    for session in get_db_session():
        return session.execute(t, bind_params)
