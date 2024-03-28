from unittest.mock import patch

from rapid.lib.exceptions import InvalidProcessError
from tests.framework.unit_test import UnitTest
from rapid.workflow.data.models import PipelineInstance
from rapid.workflow.fields_parser import FieldsParser


class TestFieldsParser(UnitTest):


    @patch('rapid.workflow.fields_parser.RelationshipParser')
    def test_empty_fields_does_nothing(self, mock_rel_parser):
        parser = FieldsParser(None, None)
        mock_rel_parser.assert_not_called()

        parser = FieldsParser(None, '')
        mock_rel_parser.assert_not_called()

        self.assertEqual({}, parser.fields_mapping())
        self.assertEqual([], parser.field_joins())

    def test_no_relationship_fields_filters_not_known_columns(self):
        parser = FieldsParser(PipelineInstance, 'status_id,id,created_date,foobar')
        self.assertEqual([], parser.field_joins())
        self.assertEqual({'pipeline_instances': ['status_id', 'id', 'created_date']}, parser.fields_mapping())

    def test_one_relationship_contract(self):
        parser = FieldsParser(PipelineInstance, 'stage_instances')
        self.assertEqual('ORM Path[Mapper[PipelineInstance(pipeline_instances)] -> PipelineInstance.stage_instances -> Mapper[StageInstance(stage_instances)]]',
                         str(parser.field_joins()[0].path))
        self.assertEqual({'pipeline_instances': ['stage_instances']}, parser.fields_mapping())

    def test_nested_relationship_contract(self):
        parser = FieldsParser(PipelineInstance, 'stage_instances;stage_instances=workflow_instances,status')
        
        self.assertEqual([
            "ORM Path[Mapper[PipelineInstance(pipeline_instances)] -> PipelineInstance.stage_instances -> Mapper[StageInstance(stage_instances)]]",
            "ORM Path[Mapper[PipelineInstance(pipeline_instances)] -> PipelineInstance.stage_instances -> Mapper[StageInstance(stage_instances)] -> StageInstance.workflow_instances -> Mapper[WorkflowInstance(workflow_instances)]]",
            "ORM Path[Mapper[PipelineInstance(pipeline_instances)] -> PipelineInstance.stage_instances -> Mapper[StageInstance(stage_instances)] -> StageInstance.status -> Mapper[Status(statuses)]]"
        ], [str(tmp.path) for tmp in parser.field_joins()])
        self.assertEqual({'pipeline_instances': ['stage_instances'], 'stage_instances': ['workflow_instances', 'status']}, parser.fields_mapping())

    def test_nested_relationship_without_first_field_definition_raises_error(self):
        parser = FieldsParser(PipelineInstance, 'stage_instances=workflow_instances')

        self.assertEqual([], parser.field_joins())
        self.assertEqual({'pipeline_instances': []}, parser.fields_mapping())
