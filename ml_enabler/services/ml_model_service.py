from flask import current_app
from ml_enabler.models.ml_model import MLModel
from ml_enabler.models.dtos.ml_model_dto import MLModelDTO
from ml_enabler.models.utils import NotFound
from ml_enabler.utils import version_to_array
from sqlalchemy.orm.exc import NoResultFound


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
        :params ml_model_dto

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
        :params model_id
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
        :params model_id

        :raises NotFound
        :returns ML Model
        """

        ml_model = MLModel.get(model_id)
        if ml_model:
            return ml_model.as_dto()
        else:
            raise NotFound('Model does not exist')

    @staticmethod
    def get_all():
        """
        Get all ML Models

        :raises NotFound
        :returns array of ML Models
        """

        ml_models = MLModel.get_all()
        if (ml_models):
            model_collection = []
            for model in ml_models:
                model_collection.append(model.as_dto().to_primitive())
            return model_collection
        else:
            raise NotFound('No models exist')

    @staticmethod
    def update_ml_model(updated_ml_model_dto: MLModelDTO) -> int:
        """
        Update an existing ML Model
        :params model_id

        :raises NotFound
        :returns model_id
        """

        ml_model = MLModel.get(updated_ml_model_dto.model_id)
        if (ml_model):
            ml_model.update(updated_ml_model_dto)
            return updated_ml_model_dto.model_id
        else:
            raise NotFound('Model does not exist')
