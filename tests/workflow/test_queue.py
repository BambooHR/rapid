import subprocess
from unittest import TestCase

from mock import Mock

from rapid.lib.work_request import WorkRequest
from rapid.workflow.queue import Queue


class TestQueue(TestCase):
    def test_trial(self):
        mock_queue_service = Mock()
        mock_queue_service.get_current_work.return_value = [WorkRequest({"executable": "remote://trial_units.sh",
                                                                        "args": "2>&1",
                                                                        "workflow_instance_id": 2,
                                                                        "_grain": "docker://rapid-base:latest",
                                                                        "cmd": "/bin/bash",
                                                                        "environment": {
                                                                            "should_fe_install": "0",
                                                                            "rapid_build": "1",
                                                                            "static_analysis_enabled": "true",
                                                                            "repository": "https://github.com/BambooHR/main.git",
                                                                            "github_user": "bretticus",
                                                                            "CIFILES_URL": "https://cifiles102.ord1.bamboohr.net",
                                                                            "is_release_branch": "0",
                                                                            "NODE_INFO": "",
                                                                            "avatar_url": "https://avatars3.githubusercontent.com/u/183433?v=4",
                                                                            "BUILD_KEY": "2af639f29b163bb8fa4b924cba68116d599f5360",
                                                                            "branch": "bmillet/grease/gm-5036-company-migration-improve-dhost-choice",
                                                                            "ssh_url": "git@github.com:BambooHR/main.git",
                                                                            "BUILD_VERSION": "19.0923.132846-f462d53",
                                                                            "commit": "",
                                                                            "NOTIFICATION_KEY": "VTJGc2RHVmtYMS9tQlh5SzdRcUVkdFdQanRPR1BiOVVQUjB2cDFKZkh5TT0K"
                                                                        },
                                                                        "headers": {
                                                                            "content-type": "application/json"
                                                                        },
                                                                        "slice": "1/1",
                                                                        "action_instance_id": 2,
                                                                        "pipeline_instance_id": 2})]
        queue = Queue(mock_queue_service, Mock(), Mock(), Mock())
        queue.process_queue([])


    def test_trial2(self):
        command = ['docker', 'run', '--volume', '"/Users/mbright/code/cihub/docker/../../rapid/rapid:/usr/local/lib/python3.7.3/lib/python3.7/site-packages/rapid"', '--add-host', '"localhost:192.168.41.115"', '--env', '"action_instance_id=2"', 'rapid-base:latest']
        child = subprocess.Popen(command)
        print(child.communicate())
