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
"""
from ddt import ddt, data, unpack
from sqlalchemy.dialects.mysql import reserved_words

from rapid.mysql_reserved_words import (
    is_mysql_url,
    register_if_mysql,
    register_mysql_reserved_words,
)
from tests.framework.unit_test import UnitTest


@ddt
class TestMysqlReservedWords(UnitTest):

    def setUp(self):
        # RESERVED_WORDS_MYSQL is a process-global set; start each test from a clean
        # slate so the register assertions are meaningful, and restore on teardown.
        super().setUp()
        self._had_manual = "manual" in reserved_words.RESERVED_WORDS_MYSQL
        reserved_words.RESERVED_WORDS_MYSQL.discard("manual")

    def tearDown(self):
        reserved_words.RESERVED_WORDS_MYSQL.discard("manual")
        if self._had_manual:
            reserved_words.RESERVED_WORDS_MYSQL.add("manual")
        super().tearDown()

    @data(
        ("mysql+mysqldb://root:pw@host/db", True),
        ("mysql://root:pw@host/db", True),
        ("sqlite:///data.db", False),
        ("postgresql://user@host/db", False),
        ("", False),
        (None, False),
    )
    @unpack
    def test_is_mysql_url(self, url, expected):
        assert is_mysql_url(url) == expected

    def test_register_adds_manual_to_dialect(self):
        register_mysql_reserved_words()
        assert "manual" in reserved_words.RESERVED_WORDS_MYSQL

    def test_register_if_mysql_registers_for_mysql(self):
        assert register_if_mysql("mysql+mysqldb://root:pw@host/db") is True
        assert "manual" in reserved_words.RESERVED_WORDS_MYSQL

    def test_register_if_mysql_skips_non_mysql(self):
        assert register_if_mysql("sqlite:///data.db") is False
        assert "manual" not in reserved_words.RESERVED_WORDS_MYSQL
