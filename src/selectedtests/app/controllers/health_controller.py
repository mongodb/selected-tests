"""Controller for the health endpoints."""
from flask import Response, jsonify
from flask_restplus import Resource, fields

from selectedtests.app.app import api

ns = api.namespace("health", description="Health check endpoint")

health_model = ns.model("HealthCheckResponse", {"online": fields.Boolean})


@ns.route("")
class Health(Resource):
    """Represents the collection of endpoints that give the health of the service."""

    @ns.response(200, "Success", health_model)
    def get(self) -> Response:
        """Get the current status of the service."""
        return jsonify({"online": True})
