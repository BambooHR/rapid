# Always prefer setuptools over distutils
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
import ssl
import sys
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

ssl._create_default_https_context = ssl._create_unverified_context

here = path.abspath(path.dirname(__file__))

if __name__ == '__main__':
    setup()

