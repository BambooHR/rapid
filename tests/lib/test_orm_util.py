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
from unittest import TestCase

from sqlalchemy import Boolean, DateTime, Integer, create_engine, insert
from sqlalchemy.orm import Session

import rapid.ci.data.models  # noqa: F401  # registers Commit and the PipelineInstance.commit backref
import rapid.qa.data.models  # noqa: F401
from rapid.lib import get_declarative_base
from rapid.lib.utils import ORMUtil
from rapid.release.data.models import Release
from rapid.workflow.data.models import PipelineInstance


class TestORMUtilFilteredQuery(TestCase):
    """Runs ORMUtil.get_filtered_query against the real models on an in-memory SQLite database."""

    def setUp(self):
        self.engine = create_engine('sqlite://')
        self.metadata = get_declarative_base().metadata
        self.metadata.create_all(self.engine)
        self.session = Session(self.engine)

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    def _insert(self, table_name, **values):
        """Inserts a row, filling NOT NULL columns the test does not care about."""
        table = self.metadata.tables[table_name]
        row = dict(values)
        for column in table.columns:
            if column.name in row or column.nullable or column.primary_key or column.default is not None:
                continue
            if isinstance(column.type, Boolean):
                row[column.name] = True
            elif isinstance(column.type, DateTime):
                row[column.name] = datetime.datetime(2026, 1, 1)
            elif isinstance(column.type, Integer):
                row[column.name] = 1
            else:
                row[column.name] = 'x'
        self.session.execute(insert(table).values(**row))

    def _ids(self, clazz, _filter):
        query = ORMUtil.get_filtered_query(self.session.query(clazz), _filter, clazz)
        return [row.id for row in query.order_by(clazz.id).all()]

    def _sql(self, clazz, _filter):
        return str(ORMUtil.get_filtered_query(self.session.query(clazz), _filter, clazz))

    def test_filters_pipeline_instances_through_the_commit_association_table(self):
        for commit_id, sha in ((1, 'sha-a'), (2, 'sha-b'), (3, 'sha-other')):
            self._insert('commits', id=commit_id, commit_identifier=sha, vcs_id=1)
        for instance_id in (10, 11, 12):
            self._insert('pipeline_instances', id=instance_id)
        for link_id, instance_id, commit_id in ((1, 10, 1), (2, 11, 2), (3, 12, 3)):
            self._insert('pipeline_instance_commits', id=link_id, pipeline_instance_id=instance_id, commit_id=commit_id)

        self.assertEqual([10, 11], self._ids(PipelineInstance, 'commit.commit_identifier_in_sha-a,sha-b'))

    def test_returns_each_root_row_once_when_several_joined_rows_match(self):
        self._insert('commits', id=1, commit_identifier='sha-a', vcs_id=1)
        self._insert('commits', id=2, commit_identifier='sha-b', vcs_id=1)
        self._insert('pipeline_instances', id=10)
        self._insert('pipeline_instance_commits', id=1, pipeline_instance_id=10, commit_id=1)
        self._insert('pipeline_instance_commits', id=2, pipeline_instance_id=10, commit_id=2)
        self._insert('pipeline_parameters', id=1, pipeline_instance_id=10, parameter='branch', value='main')
        self._insert('pipeline_parameters', id=2, pipeline_instance_id=10, parameter='base', value='main')

        self.assertEqual([10], self._ids(PipelineInstance, 'commit.commit_identifier_in_sha-a,sha-b'))
        self.assertEqual([10], self._ids(PipelineInstance, 'parameters.value_eq_main'))

    def test_filters_release_steps_integrations_through_the_step_association_table(self):
        # Release 1's own integration is 100; its step's integration is 200.
        self._insert('integrations', id=100, value='release-level')
        self._insert('integrations', id=200, value='step-level')
        self._insert('releases', id=1, integration_id=100, commit_id=1)
        self._insert('steps', id=1, release_id=1)
        self._insert('step_integrations', id=1, step_id=1, integration_id=200)

        self.assertEqual([1], self._ids(Release, 'steps.integrations.value_eq_step-level'))
        self.assertEqual([], self._ids(Release, 'steps.integrations.value_eq_release-level'))

    def test_column_only_filter_does_not_add_distinct(self):
        self.assertNotIn('DISTINCT', self._sql(PipelineInstance, 'status_id_eq_1'))

    def test_relationship_filter_adds_distinct(self):
        self.assertIn('SELECT DISTINCT', self._sql(PipelineInstance, 'parameters.value_eq_main'))
