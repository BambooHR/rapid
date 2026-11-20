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
from unittest.mock import Mock

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from rapid.qa.data.dals.qa_dal import QaDal
from rapid.qa.data.models import QaArea, QaBehaviorPoint, QaFeature, QaTest, QaTestHistory, QaTestMapping, Stacktrace
from rapid.testmapper import PythonFile
from tests.framework.unit_test import UnitTest


class TestQaDal(UnitTest):

    def _create_database(self, models=(QaTest, QaTestHistory, Stacktrace)):
        database = create_engine('sqlite://')
        for model in models:
            model.__table__.create(database)
        return database

    def test_parse_action(self):
        python_file = PythonFile(None, None)

        self.assertEqual("unit", python_file.parse_action("@rapid-unit Test:Test:Testing"))
        self.assertEqual("unit", python_file.parse_action("rapid-unit: Test:Test:Testing"))
        self.assertEqual(None, python_file.parse_action("@@@@rapid-unit12: Test:Test:Testing"))

    def test_save_results_normalizes_test_names_into_single_qa_tests(self):
        with Session(self._create_database()) as session:
            existing = QaTest(name='Test: returns null on 409')
            session.add(existing)
            session.commit()

            QaDal().save_results(Mock(id=1, pipeline_instance_id=1), session, {'results': {
                'File: get-body-sections.\n\n    spec.js': {'time': 1},
                '  File: get-body-sections.  spec.js ': {'time': 2},
                'Test:\n    returns null on 409': {'time': 3},
                'foo\x00bar': {'time': 4},
                'foo\x1bbar': {'time': 5},
                '\x1b[31mfoo\x1b[39mbar': {'time': 6},
            }})

            self.assertEqual({'File: get-body-sections. spec.js', 'Test: returns null on 409', 'foobar'},
                             {qa_test.name for qa_test in session.query(QaTest)})
            self.assertEqual(3, session.query(QaTest).count())
            self.assertEqual(existing.id,
                             session.query(QaTest).filter(QaTest.name == 'Test: returns null on 409').one().id)
            self.assertEqual([('File: get-body-sections. spec.js', 1), ('File: get-body-sections. spec.js', 2),
                              ('Test: returns null on 409', 3), ('foobar', 4), ('foobar', 5), ('foobar', 6)],
                             sorted((history.test.name, history.duration) for history in session.query(QaTestHistory)))

    def test_get_area_mapper_normalizes_and_chunks_qa_test_lookup(self):
        database = self._create_database((QaArea, QaFeature, QaBehaviorPoint, QaTest, QaTestMapping))
        lookup_sizes = []

        @event.listens_for(database, 'before_cursor_execute')
        def record_lookup(conn, cursor, statement, parameters, context, executemany):
            if statement.startswith('SELECT') and 'FROM qa_tests' in statement:
                lookup_sizes.append(len(parameters))

        with Session(database) as session:
            existing = QaTest(name='Test: returns null on 409')
            session.add(existing)
            session.commit()

            tests = [{'name': 'Test:\n    returns null on 409'}]
            tests.extend({'name': 'test {}'.format(index)} for index in range(1000))
            QaDal()._get_area_mapper(session, 1, {'Area': {'Feature': {'Behavior': tests}}})

            self.assertEqual([1000, 1], lookup_sizes)
            mapping = session.query(QaTestMapping).one()
            self.assertEqual(existing.id, mapping.test_id)

    def test_save_results_chunks_qa_test_lookup(self):
        database = self._create_database()
        lookup_sizes = []

        @event.listens_for(database, 'before_cursor_execute')
        def record_lookup(conn, cursor, statement, parameters, context, executemany):
            if statement.startswith('SELECT') and 'FROM qa_tests' in statement:
                lookup_sizes.append(len(parameters))

        with Session(database) as session:
            QaDal().save_results(Mock(id=1, pipeline_instance_id=1), session,
                                 {'results': {'test {}'.format(index): {'time': 1} for index in range(2500)}})

            self.assertEqual([1000, 1000, 500], lookup_sizes)
            self.assertEqual(2500, session.query(QaTest).count())
            self.assertEqual(2500, session.query(QaTestHistory).count())

    def test_save_results_logs_and_raises_failed_qa_test_lookup(self):
        session = Mock()
        session.query.side_effect = Exception("Illegal mix of collations for operation ' IN '")

        with self.assertLogs('rapid', level='ERROR') as logs, self.assertRaises(Exception):
            QaDal().save_results(Mock(id=7), session, {'results': {'plain test': {}, 'caf\u00e9 test': {}}})

        self.assertIn("action instance 7: chunk size 2, first name 'plain test', 1 non-ASCII names ['caf\u00e9 test']",
                      logs.output[0])
