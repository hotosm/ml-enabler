from flask_restful import Resource, request, current_app
from ml_enabler.models.dtos.ml_model_dto import MLModelDTO
from schematics.exceptions import DataError
from ml_enabler.services.ml_model_service import MLModelService
from ml_enabler.models.utils import NotFound
from sqlalchemy.exc import IntegrityError


class StatusCheckAPI(Resource):
    """
    Healthcheck method
    ---
    produces:
        - application/json
    responses:
        200:
            description: API status check success
    """

    def get(self):
        return {'hello': 'world'}, 200


class MLModelAPI(Resource):

    def post(self):
        """
        Subscribe a new ML model
        ---
        produces:
            - application/json
        parameters:
            - in: body
              name: body
              required: true
              type: string
              description: JSON object of model information
              schema:
                properties:
                    name:
                        type: string
                        description: name of the ML model
                    source:
                        type: string
                        description: source of the ML model
                    dockerhub_hash:
                        type: string
                        description: dockerhub hash
                    dockerhub_url:
                        type: string
                        description: dockerhub url
        responses:
            200:
                description: ML Model subscribed
            400:
                description: Invalid Request
            500:
                description: Internal Server Error
        """
        try:
            model_dto = MLModelDTO(request.get_json())
            current_app.logger.info(f'request: {str(request.get_json())}')
            model_dto.validate()
            model_id = MLModelService.subscribe_ml_model(model_dto)
            return {"model_id": model_id}, 200
        except DataError as e:
            current_app.logger.error(f'Error validating request: {str(e)}')
            return str(e), 400
        except IntegrityError as e:
            current_app.logger.error(f'A model with the same name already exists: {str(e)}')
            return str(e), 400

    def delete(self, model_id):
        """
        Deletes an existing model and it's predictions
        ---
        produces:
            - application/json
        parameters:
            in: path
            name: model_id
            description: ID of the Model to be deleted
            required: true
            type: integer
        responses:
            200:
                description: ML Model deleted
            404:
                description: Model doesn't exist
            500:
                description: Internal Server Error
        """
        try:
            MLModelService.delete_ml_model(model_id)
            return {"success": "model deleted"}, 200
        except NotFound:
            return {"error": "model not found"}, 404
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return {"error": error_msg}

    def get(self, model_id):
        """
        Get model information with the ID
        ---
        produces:
            - application/json
        parameters:
            in: path
            name: model_id
            description: ID of the Model to be fetched
            required: true
            type: integer
        responses:
            200:
                description: ML Model information
            404:
                description: Model doesn't exist
            500:
                description: Internal Server Error
        """
        try:
            ml_model_dto = MLModelService.get_ml_model_by_id(model_id)
            return ml_model_dto.to_primitive(), 200
        except NotFound:
            return {"error": "model not found"}, 404
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return {"error": error_msg}

    def put(self, model_id):
        """
        Update an existing model
        produces:
            - application/json
        parameters:
            in: path
            name: model_id
            description: ID of the Model to update
            required: true
            type: integer
            - in: body
              name: body
              required: true
              type: string
              description: JSON object of model information
              schema:
                properties:
                    name:
                        type: string
                        description: name of the ML model
                    source:
                        type: string
                        description: source of the ML model
                    dockerhub_hash:
                        type: string
                        description: dockerhub hash
                    dockerhub_url:
                        type: string
                        description: dockerhub url
        responses:
            200:
                description: Updated model information
            404:
                description: Model doesn't exist
            500:
                description: Internal Server Error
        """
        try:
            updated_model_dto = MLModelDTO(request.get_json())
            print(updated_model_dto.to_primitive())
            updated_model_dto.validate()
            model_id = MLModelService.update_ml_model(updated_model_dto)
            return {"model_id": model_id}, 200
        except NotFound:
            return {"error": "model not found"}, 404
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return {"error": error_msg}
