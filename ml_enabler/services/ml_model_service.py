from flask import current_app
from ml_enabler.models.ml_model import MLModel, MLModelVersion
from ml_enabler.models.dtos.ml_model_dto import MLModelDTO, MLModelVersionDTO
from ml_enabler.models.utils import NotFound, VersionNotFound
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
        :param model_id

        :raises NotFound
        :returns model_id
        """

        ml_model = MLModel.get(updated_ml_model_dto.model_id)
        if (ml_model):
            ml_model.update(updated_ml_model_dto)
            return updated_ml_model_dto.model_id
        else:
            raise NotFound('Model does not exist')


class MLModelVersionService():
    @staticmethod
    def get_version_by_model_version(model_id: int, version: str):
        """
        Get the version of the given model
        :param model_id, version

        :raises NotFound
        :returns MLModelVersion
        """
        try:
            version_array = version_to_array(version)
            model_version = MLModelVersion.get_version(model_id, version_array[0], version_array[1], version_array[2])
            return model_version.as_dto()
        except NoResultFound:
            raise VersionNotFound('This version of the model is not registered')

    @staticmethod
    def create_version(version_dto: MLModelVersionDTO) -> int:
        """
        Create a new version of an ML Model
        :param version_dto

        :raises DataError
        :returns version ID
        """

        new_version = MLModelVersion()
        new_version.create(version_dto)
        return new_version.id
