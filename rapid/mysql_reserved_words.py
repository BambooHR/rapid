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
 has not caught up. Without this registration SQLAlchemy emits the `manual` column
 unquoted and MySQL 8.4 rejects it with ER_PARSE_ERROR (1064) -- in both ORM queries and
 Alembic-generated DDL (op.create_table references the bare column too, which per-column
 quote=True on the model does NOT fix).

 Registering the word in the dialect's reserved-word set auto-quotes the identifier across
 every table, query, and migration -- no per-column annotation required. It mutates a
 process-global SQLAlchemy set, so it must run BEFORE any engine/dialect is created or any
 statement is compiled; it is invoked from rapid/__init__.py (the package root, the
 earliest point that runs in every DB entry point).
"""
from sqlalchemy.dialects.mysql import reserved_words

# MySQL 8.4 reserved words absent from SQLAlchemy's RESERVED_WORDS_MYSQL. Only `manual` is
# used as an identifier in rapid today; add others here (e.g. parallel/qualify/tablesample)
# if a future column reuses them.
_MYSQL_8_4_RESERVED_WORDS = frozenset({"manual"})


def register_mysql_reserved_words():
    """Add MySQL 8.4 reserved words to SQLAlchemy's MySQL dialect. Idempotent."""
    reserved_words.RESERVED_WORDS_MYSQL.update(_MYSQL_8_4_RESERVED_WORDS)
