"""Controller for the health endpoints."""
from flask import jsonify
from flask_restplus import Api, Resource, fields


def add_health_endpoints(api: Api):
    """
    Add to the given app instance the health endpoints of the service.

    :param api: An instance of a Flask Restplus Api that wraps a Flask instance
    """
    ns = api.namespace("health", description="Health check endpoint")

    health_model = ns.model("HealthCheckResponse", {"online": fields.Boolean})

    @ns.route("")
    class Health(Resource):
        """Represents the collection of endpoints that give the health of the service."""

        @ns.response(200, "Success", health_model)
        def get(self):
            """Get the current status of the service."""
            return jsonify({"online": True})
