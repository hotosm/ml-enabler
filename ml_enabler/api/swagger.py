from flask import current_app, jsonify
from flask_restful import Resource
from flask_swagger import swagger


class SwaggerDocsAPI(Resource):
    """
    Provides a swagger template for API docs
    """

    def get(self):
        template = swagger(current_app)
        template['info']['title'] = "HOT ML Enabler API"
        template['info']['description'] = "API endpoints for HOT ML Enabler"
        template['info']['version'] = "0.0.1"

        return jsonify(template)
