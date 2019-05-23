from flask import current_app
from ml_enabler.models.ml_model import MLModel
from ml_enabler.models.dtos.ml_model_dto import MLModelDTO
from ml_enabler.models.utils import NotFound

class MLModelServiceError(Exception):
    """ Custom Exception to notify callers an error occurred when validating an ML Model """

    def __init__(self, message):
        if current_app:
            current_app.logger.error(message)


class MLModelService():
    @staticmethod
    def subscribe_ml_model(ml_model_dto: MLModelDTO) -> int:
        """
        Subscribes an ML Model by saving it in the database
        :param ml_model_dto

        :raises DataError
        :returns ID of the ml model
        """

        new_ml_model = MLModel()
        new_ml_model.create(ml_model_dto)
        current_app.logger.info(new_ml_model)
        return new_ml_model.id

    @staticmethod
    def delete_ml_model(model_id: int):
        """
        Deletes ML model and associated predictions
        :param model_id
        """
        ml_model = MLModel.get(model_id)
        if ml_model:
            ml_model.delete()
        else:
            raise NotFound('Model does not exist')

    @staticmethod
    def get_ml_model_by_id(model_id: int):
        """
        Get an ML Model for a given ID
        :param model_id

        :raises NotFound
        :returns ML Model
        """

        ml_model = MLModel.get(model_id)
        if ml_model:
            return ml_model.as_dto()
        else:
            raise NotFound('Model does not exist')
