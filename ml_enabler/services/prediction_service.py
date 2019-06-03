from flask import current_app
from ml_enabler.models.ml_model import MLModel, MLModelVersion, Prediction
from ml_enabler.models.dtos.ml_model_dto import MLModelDTO, MLModelVersionDTO, PredictionDTO
from ml_enabler.models.utils import NotFound, VersionNotFound, version_to_array
from sqlalchemy.orm.exc import NoResultFound


class PredictionService():
  @staticmethod
  def create(model_id: int, version_id: int, payload: dict) -> int:
    """
    Validate and add predictions from a model to the database
    :params model_id, version_id, payload

    :raises DataError
    :returns ID of the prediction
    """

    prediction_dto = PredictionDTO()
    prediction_dto.model_id = model_id
    prediction_dto.version_id = version_id
    prediction_dto.bbox = payload['bbox']
    prediction_dto.predictions = payload['predictions']
    prediction_dto.validate()

    new_prediction = Prediction()
    new_prediction.create(prediction_dto)
    return new_prediction.id
