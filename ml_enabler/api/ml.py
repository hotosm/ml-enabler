from flask_restful import Resource, request, current_app
from ml_enabler.models.dtos.ml_model_dto import MLModelDTO, MLModelVersionDTO, PredictionDTO
from schematics.exceptions import DataError
from ml_enabler.services.ml_model_service import MLModelService, MLModelVersionService
from ml_enabler.services.prediction_service import PredictionService
from ml_enabler.models.utils import NotFound, VersionNotFound, version_to_array
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
            - in: path
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
            - in: path
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
        ---
        produces:
            - application/json
        parameters:
            - in: path
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


class GetAllModels(Resource):
    """ Methods to fetch many ML models """
    def get(self):
        """
        Get all ML models
        ---
        produces:
            - application/json
        responses:
            200:
                description: List of ML models
            404:
                description: No models found
            500:
                description: Internal Server Error
        """
        try:
            ml_models = MLModelService.get_all()
            return ml_models, 200
        except NotFound:
            return {"error": "no models found"}, 404
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return {"error": error_msg}


class PredictionAPI(Resource):
    """ Methods to manage ML predictions """

    def post(self, model_id):
        """
        Store predictions for an ML Model
        ---
        produces:
            - application/json
        parameters:
            - in: body
              name: body
              required: true
              type: string
              description: JSON object of predictions
              schema:
                properties:
                    modelId:
                        type: integer
                        description: ML Model ID
                        required: true
                    version:
                        type: string
                        description: semver version of the Model
                        required: true
                    dockerhub_hash:
                        type: string
                        description: dockerhub hash
                        required: false
                    bbox:
                        type: array of floats
                        description: BBOX of the predictions
                        required: true
        responses:
            200:
                description: ID of the prediction
            400:
                description: Invalid Request
            500:
                description: Internal Server Error
        """
        try:
            payload = request.get_json()
            print(payload)
            version = payload['version']

            # check if this model exists
            ml_model_dto = MLModelService.get_ml_model_by_id(model_id)

            # check if the version is registered
            model_version = MLModelVersionService.get_version_by_model_version(model_id, version)
            prediction_id = PredictionService.create(model_id, model_version.version_id, payload)
            return {"prediction_id": prediction_id}, 200

        except VersionNotFound:
            # if not, add it
            try:
                version_array = version_to_array(version)
                version_dto = MLModelVersionDTO()
                version_dto.model_id = model_id
                version_dto.version_major = version_array[0]
                version_dto.version_minor = version_array[1]
                version_dto.version_patch = version_array[2]
                version_id = MLModelVersionService.create_version(version_dto)

                prediction_id = PredictionService.create(model_id, version_id, payload)
                return {"prediction_id": prediction_id}, 200
            except DataError as e:
                current_app.logger.error(f'Error validating request: {str(e)}')
                return str(e), 400
            except Exception as e:
                error_msg = f'Unhandled error: {str(e)}'
                current_app.logger.error(error_msg)
                return {"error": error_msg}, 500
        except NotFound:
            return {"error": "model not found"}, 404
        except DataError as e:
            current_app.logger.error(f'Error validating request: {str(e)}')
            return str(e), 400
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return {"error": error_msg}, 500
