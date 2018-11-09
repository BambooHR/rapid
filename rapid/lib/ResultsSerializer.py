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
from rapid.lib.WrappingThreadPool import WrappingThreadPool


class ResultsSerializer(object):

    @staticmethod
    def serialize_results(results, allowed_children=None, previous_children=None, thread_count=5):
        with WrappingThreadPool(thread_count) as pool:
            return pool.map(ResultsSerializer._convert, ResultsSerializer._get_results_generator(results, allowed_children, previous_children))

    @staticmethod
    def _convert(x):
        (result, allowed_children, previous_children) = x
        return result.serialize(allowed_children, previous_children)

    @staticmethod
    def _get_results_generator(results, allowed_children, previous_children):
        for qaTestMapping in results:
            yield (qaTestMapping, allowed_children, previous_children)
