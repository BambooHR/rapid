import flask

from rapid.lib import Injectable


class HTTPWrapper(Injectable):

    def current_request(self) -> flask.Request:
        return flask.request
