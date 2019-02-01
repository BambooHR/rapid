"""
Copyright (c) 2018 Michael Bright and Bamboo HR LLC

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


class ConfigurationGenerator(object):
    """
    ConfigurationGenerator is used to generator a configuration file for rapid.
    """
    def generate(self, config_type):
        config = None
        if config_type == 'master':
            from rapid.master.MasterConfiguration import MasterConfiguration
            config = MasterConfiguration()

        elif config_type == 'client':
            from rapid.client.client_configuration import ClientConfiguration
            config = ClientConfiguration()
        self.gather_output(config)

    def gather_output(self, config):
        for key, value in config.__dict__.items():
            read_input = None
            try:
                read_input = raw_input("Enter value for '{}'[{}]? ".format(key, value))
            except NameError:
                read_input = input(prompt="Enter the value for '{}'[{}]? ".format(key, value))

            if not read_input:
                read_input = value

            setattr(config, key, read_input)

        print(config.__dict__)
