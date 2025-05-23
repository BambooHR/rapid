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
__version__ = '0.0.0'

try:
    from importlib_metadata import version
    __version__ = version('rapid-framework')
except ImportError:
    ...



class Version(object):
    HEADER = 'X-RAPIDCI-VERSION'

    @staticmethod
    def get_version():
        return __version__
