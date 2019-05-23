from flask_restful import Resource, request, current_app
from ml_enabler.models.dtos.ml_model_dto import MLModelDTO
from schematics.exceptions import DataError
from ml_enabler.services.ml_model_service import MLModelService
from ml_enabler.models.utils import NotFound
from sqlalchemy.exc import IntegrityError

class StatusCheckAPI(Resource):
    """ Healthcheck method """

    def get(self):
        return {'hello': 'world'}, 200


class MLModelAPI(Resource):

    def post(self):
        """ Subscribe a new ML model """
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
        """ Update an existing model """
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
