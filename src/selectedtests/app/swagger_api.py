"""A wrapper around the Flask Restplus APi to help with swagger routing issues in Kanopy."""
from flask import url_for
from flask_restplus import Api


class Swagger_Api(Api):
    """Wrapper created by solution from https://github.com/noirbizarre/flask-restplus/issues/223."""

    @property
    def specs_url(self):
        """
        Swagger specifications absolute url (ie. `swagger.json`).

        :rtype: str
        """
        return url_for(self.endpoint("specs"), _external=False)
