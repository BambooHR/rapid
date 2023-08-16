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
from tests.framework.unit_test import UnitTest

try:
    import simplejson as json
except:
    import json

from mock import MagicMock
from mock.mock import Mock

from rapid.lib.work_request import WorkRequest, WorkRequestEncoder


class TestWorkRequest(UnitTest):

    def test_prepare_to_send_with_hash(self):
        work_request = WorkRequest()
        work_request.prepare_to_send({'action_instance_id': 1, 'pipeline_instance_id': 2, 'grain': 'foobar'})

        self.assertEqual(1, work_request.action_instance_id)
        self.assertEqual(2, work_request.pipeline_instance_id)
        self.assertEqual('foobar', work_request.grain)

    def test_prepare_to_send_with_hash_with__grain(self):
        work_request = WorkRequest()
        work_request.prepare_to_send({'action_instance_id': 1, 'pipeline_instance_id': 2, '_grain': 'foobar'})

        self.assertEqual(1, work_request.action_instance_id)
        self.assertEqual(2, work_request.pipeline_instance_id)
        self.assertEqual('foobar', work_request.grain)

    def test_prepare_to_send_with_obj(self):
        mock_obj = MagicMock(action_instance_id=1, pipeline_instance_id=2, grain='foobar1')
        del mock_obj._grain

        work_request = WorkRequest()
        work_request.prepare_to_send(mock_obj)

        self.assertEqual(1, work_request.action_instance_id)
        self.assertEqual(2, work_request.pipeline_instance_id)
        self.assertEqual('foobar1', work_request.grain)

    def test_prepare_to_send_with_obj_with__grain(self):
        mock_obj = MagicMock(action_instance_id=1, pipeline_instance_id=2, _grain='foobar')
        del mock_obj.grain

        work_request = WorkRequest()
        work_request.prepare_to_send(mock_obj)

        self.assertEqual(1, work_request.action_instance_id)
        self.assertEqual(2, work_request.pipeline_instance_id)
        self.assertEqual('foobar', work_request.grain)

    def test_generate_from_request(self):
        mock_obj = MagicMock()
        mock_obj.json = {'action_instance_id': 1, 'pipeline_instance_id': 2, '_grain': 'foobar'}

        work_request = WorkRequest()
        work_request.generate_from_request(mock_obj)

        self.assertEqual(1, work_request.action_instance_id)
        self.assertEqual(2, work_request.pipeline_instance_id)
        self.assertEqual('foobar', work_request.grain)

    def test_generate_from_request_with_grain(self):
        mock_obj = MagicMock()
        mock_obj.json = {'action_instance_id': 1, 'pipeline_instance_id': 2, 'grain': 'foobar'}

        work_request = WorkRequest()
        work_request.generate_from_request(mock_obj)

        self.assertEqual(1, work_request.action_instance_id)
        self.assertEqual(2, work_request.pipeline_instance_id)
        self.assertEqual('foobar', work_request.grain)

    def test_jsonify(self):
        work_request = WorkRequest({'action_instance_id': 1, 'pipeline_instance_id': 2})

        self.assertEqual(json.loads('{"executable": null, "environment": {}, "headers": {"content-type": "application/json"}, "cmd": null, "args": null, "slice": null, "workflow_instance_id": null, "action_instance_id": 1, "pipeline_instance_id": 2, "grain": null, "configuration": null}'), json.loads(json.dumps(work_request, cls=WorkRequestEncoder)))

    def test_get_state_is_not_the_same_object(self):
        work_request = WorkRequest({'action_instance_id': 1})

        self.assertEqual(work_request.__dict__, work_request.__getstate__())
        self.assertTrue(id(work_request.__dict__) != id(work_request.__getstate__()), "Dict should not be the same memory location, should be a copy.")

    def test_invalid_key_will_not_error(self):
        work_request = WorkRequest()

        work_request.generate_from_request(Mock(json={"bogus": "bogus_2"}))

    def test_invalid_key_will_not_error_preparing(self):
        work_request = WorkRequest(BogusObject())

    def test_dynamic_grain_none_set(self):
        work_request = WorkRequest({"grain": "trial;testing;what"})
        self.assertEqual("trial;testing;what", work_request.grain)

    def test_dynamic_grain_found(self):
        work_request = WorkRequest({"environment": {"foo": "cool"}, "grain": '{foo}'})
        self.assertEqual("cool", work_request.grain)

    def test_dynamic_grain_multiple_found(self):
        work_request = WorkRequest({"environment": {"foo": "cool", "bar": "stuff"}, "grain": '{foo};{bar}'})
        self.assertEqual("cool;stuff", work_request.grain)

    def test_dynamic_grain_one_found(self):
        work_request = WorkRequest({"environment": {"foo": "cool"}, "grain": '{foo};{bar}'})
        self.assertEqual("cool;{bar}", work_request.grain)


class BogusObject(object):
    pass
