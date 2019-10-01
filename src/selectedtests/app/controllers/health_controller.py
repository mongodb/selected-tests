from flask import jsonify
from flask_restplus import Api, Resource, fields


def add_health_endpoints(api: Api):

    ns = api.namespace("health", description="Health check endpoint")

    health_model = ns.model("HealthCheckResponse", {"online": fields.Boolean})

    @ns.route("")
    class Health(Resource):
        @ns.response(200, "Success", health_model)
        def get(self):
            """
            Get the current status of the service
            """
            return jsonify({"online": True})
