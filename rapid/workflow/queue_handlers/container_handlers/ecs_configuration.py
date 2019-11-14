import json
from rapid.lib.configuration import Configuration, ConfigurationDefaults


class ECSConfiguration(Configuration):
    NOT_SET = "__NOT_SET__"

    def __init__(self, file_name=None):
        self.maximum_task_time = 20
        self.aws_access_key_id = None
        self.aws_secret_access_key = None
        self.aws_session_token = None
        self.region_name = None

        self.cluster = None
        self.taskDefinition = None
        self.count = None
        self.startedBy = None
        self.group = None
        self.placementConstraints = None
        self.placementStrategy = None
        self.launchType = None
        self.platformVersion = None
        self.networkConfiguration = None
        self.tags = None
        self.enableECSManagedTags = None
        self.propogateTags = None

        super(ECSConfiguration, self).__init__(file_name)

    @property
    def section_mapping(self):
        default_config = ConfigurationDefaults(self.NOT_SET, str)
        return {
            'general': {
                'maximum_task_time': ConfigurationDefaults(20*60, int)  # 20 minutes
            },
            'aws_credentials': {
                'aws_access_key_id': default_config,
                'aws_secret_access_key': default_config,
                'aws_session_token': default_config,
                'region_name': default_config,
            },
            'task_defaults': {
                'cluster': default_config,
                'taskDefinition': default_config,
                'overrides': ConfigurationDefaults(self.NOT_SET, dict),
                'count': default_config,
                'startedBy': default_config,
                'group': default_config,
                'placementConstraints': ConfigurationDefaults(self.NOT_SET, list),
                'placementStrategy': ConfigurationDefaults(self.NOT_SET, list),
                'launchType': default_config,
                'platformVersion': default_config,
                'networkConfiguration': ConfigurationDefaults(self.NOT_SET, dict),
                'tags': ConfigurationDefaults(self.NOT_SET, list),
                'enableECSManagedTags': ConfigurationDefaults(self.NOT_SET, bool),
                'propogateTags': default_config
            }
        }

    @property
    def aws_credentials(self):
        # type: () -> dict
        return self._get_section_values('aws_credentials')

    @property
    def default_task_definition(self):
        # type: () -> dict
        return self._get_section_values('task_defaults')

    def _get_section_values(self, section):
        return {key: getattr(self, key) for key in self.section_mapping[section].keys() if getattr(self, key) != self.NOT_SET}

    def _handle_normal_value(self, parser, key, section, type_cast):
        new_value = parser.get(section, key)
        try:
            if type_cast in [list, dict]:
                setattr(self, key, type_cast(json.loads(new_value)))
            else:
                setattr(self, key, type_cast(new_value))
        except ValueError:
            setattr(self, key, type_cast(new_value))
