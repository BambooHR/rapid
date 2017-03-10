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
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

ssl._create_default_https_context = ssl._create_unverified_context

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

execfile('./rapid/lib/Version.py')

requirements = [
    'flask',
    'requests==2.7.0',
    'futures',
    'jsonpickle',
    'enum34==1.0.4',
    'simplejson==3.10.0'
]

setup(
        name='rapid-framework',
        version=__version__,
        description='Rapid Framework',
        long_description=long_description,

        # The project's main homepage.
        url='https://github.com/BambooHR/rapid',

        # Author details
        author='Michael Bright',
        author_email='mbright@bamboohr.com',

        # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
        classifiers=[
            # How mature is this project? Common values are
            #   3 - Alpha
            #   4 - Beta
            #   5 - Production/Stable
            'Development Status :: 4 - Beta',

            # Indicate who your project is intended for
            'Topic :: Software Development :: Build Tools',

            # Specify the Python versions you support here. In particular, ensure
            # that you indicate whether you support Python 2, Python 3 or both.
            'Programming Language :: Python :: 2.7'
        ],

        # What does your project relate to?
        keywords='internal ci jenkinskiller',

        # You can just specify the packages manually here if your project is
        # simple. Or you can use find_packages().
        packages=find_packages(exclude=['contrib', 'docs', 'tests*']),

        # List run-time dependencies here.  These will be installed by pip when
        # your project is installed. For an analysis of "install_requires" vs pip's
        # requirements files see:
        # https://packaging.python.org/en/latest/requirements.html
        install_requires=requirements,

        # List additional groups of dependencies here (e.g. development
        # dependencies). You can install these using the following syntax,
        # for example:
        # $ pip install -e .[dev,test]
        extras_require={
            'test': ['coverage', 'nose'],
            'master': ['alembic', 'SQLAlchemy==1.0.6', 'Flask-SQLAlchemy==2.0', 'mysql-python', 'pygithub'],
            'client': []
        },

        # To provide executable scripts, use entry points in preference to the
        # "scripts" keyword. Entry points provide cross-platform support and allow
        # pip to create the appropriate form of executable for the target platform.
        entry_points={
            'console_scripts': [
                'rapid=rapid.__main__:main',
            ],
        },
)

