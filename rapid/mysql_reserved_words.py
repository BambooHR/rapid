"""
 Copyright (c) 2025 Michael Bright and Bamboo HR LLC

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

 http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.

 Register MySQL reserved words that SQLAlchemy's MySQL dialect does not yet quote.

 MySQL 8.4 promoted MANUAL to a reserved word, but SQLAlchemy's RESERVED_WORDS_MYSQL set
 has not caught up. Without this, SQLAlchemy emits the `manual` column unquoted and MySQL
 8.4 rejects it with ER_PARSE_ERROR (1064) -- in both ORM queries and Alembic DDL
 (op.create_table references the bare column, which per-column quote=True does NOT fix).

 register_if_mysql() detects the backend from the connection string and only imports/
 registers for MySQL, so non-MySQL deployments (e.g. SQLite, which the tests use) never
 import the MySQL dialect or touch its reserved-word set. It must be called BEFORE the
 engine / identifier-preparer is created -- registering afterward has no effect, due to
 dialect/statement caching -- so it is wired into configure_data_layer() (master app) and
 the Alembic env.py, each of which knows the connection string before building the engine.
"""

# MySQL 8.4 reserved words absent from SQLAlchemy's RESERVED_WORDS_MYSQL. Only `manual` is
# used as an identifier in rapid today; add others (parallel/qualify/tablesample) here if a
# future column reuses them.
_MYSQL_8_4_RESERVED_WORDS = frozenset({"manual"})


def is_mysql_url(db_connect_string):
    """Return True if the connection string targets a MySQL backend (any driver)."""
    if not db_connect_string:
        return False
    from sqlalchemy.engine.url import make_url
    return make_url(db_connect_string).get_backend_name() == "mysql"


def register_mysql_reserved_words():
    """Add the MySQL 8.4 reserved words to SQLAlchemy's MySQL dialect set. Idempotent."""
    from sqlalchemy.dialects.mysql import reserved_words
    reserved_words.RESERVED_WORDS_MYSQL.update(_MYSQL_8_4_RESERVED_WORDS)


def register_if_mysql(db_connect_string):
    """Register the MySQL 8.4 reserved words only when the DB is MySQL.

    Returns True if registration ran, False otherwise. Detects the backend from the URL so
    non-MySQL setups never import the MySQL dialect. Must run before the engine is created.
    """
    if not is_mysql_url(db_connect_string):
        return False
    register_mysql_reserved_words()
    return True
