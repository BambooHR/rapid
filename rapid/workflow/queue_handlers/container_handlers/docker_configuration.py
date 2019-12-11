import re

from rapid.lib.work_request import WorkRequest


class DockerConfiguration(object):
    _acceptable = [
        'add-host', 'env', 'volume'
    ]

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if key in self._acceptable:
                setattr(self, key, value)

    def get_string_rep(self, work_request):
        # type: (WorkRequest) -> str
        string_list = []
        keys = sorted(self.__dict__.keys())
        for key in keys:
            value = getattr(self, key)
            if isinstance(value, list):
                string_list.extend(['--{}={}'.format(key, self._get_substituted_value(work_request, tmp_value)) for tmp_value in value])
            else:
                string_list.append('--{}={}'.format(key, self._get_substituted_value(work_request, value)))
        return ' '.join(string_list)

    def _get_substituted_value(self, work_request, string):
        if '(' in string:
            try:
                for match in re.findall(r'\([\w_]*\)', string):
                    token = match.split('(')[1].split(')')[0]
                    try:
                        string = string.replace(match, '{}={}'.format(token, getattr(work_request, token)))
                    except AttributeError:
                        pass
            except (TypeError, AttributeError) as exception:
                pass
        return string
