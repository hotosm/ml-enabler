from ml_enabler.models.ml_model import Imagery
from ml_enabler.models.utils import ImageryNotFound
from ml_enabler import db

class ImageryService():
    @staticmethod
    def create(model_id: int,  payload: dict) -> int:
        """
        Validate and add imagery from a model to the database

        :params model_id, payload

        :raises DataError
        :returns ID of the prediction
        """

        imagery = Imagery.create(payload)

        return new_prediction.id

    @staticmethod
    def patch(imagery_id: int, update: dict) -> int:
        """
        Patch a prediction by ID
        :params prediction_id
        :params update
        :returns prediction
        """

        imagery = Imagery.get(imagery_id)

        if (imagery):
            prediction.link(update)

            return prediction_id
        else:
            raise NotFound('Prediction does not exist')

    @staticmethod
    def get(imagery_id: int):
        """
        Fetch imagery source by id
        :params imagery_id

        :raises ImagerysNotFound
        :returns imagery
        """

        return {}

