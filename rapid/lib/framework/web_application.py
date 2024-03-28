from typing import Callable, List


class WebApplication:

    def __init__(self, application_framework):
        self.application_framework = application_framework
        self._is_flask = hasattr(application_framework, 'add_url_rule')
        self._is_fastapi = hasattr(application_framework, 'add_api_route')

    def add_url_rule(self, rule: str, endpoint: str, routable: Callable, methods: List[str]):
        if self._is_flask:
            self.application_framework.add_url_rule(rule, endpoint, routable, methods)
        if self._is_fastapi:
            self.application_framework.add_api_route(rule, routable, methods=methods)
