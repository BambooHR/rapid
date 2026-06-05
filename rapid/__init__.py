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
# Register MySQL 8.4 reserved words (e.g. `manual`) so SQLAlchemy auto-quotes them across
# all tables, queries, and migrations. Done at the package root -- the earliest point that
# runs in every DB entry point (master app + alembic env.py) before any engine/compilation.
# Guarded for environments without SQLAlchemy (the rapid client has no DB dependency).
import importlib.util as _importlib_util

if _importlib_util.find_spec("sqlalchemy") is not None:
    from rapid.mysql_reserved_words import register_mysql_reserved_words

    register_mysql_reserved_words()
