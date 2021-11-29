from ml_enabler.models.imagery import Imagery
from ml_enabler.models.utils import ImageryNotFound
from ml_enabler import db

class ImageryService():
    @staticmethod
    def create(model_id: int,  payload: dict) -> int:
        """
        Validate and add imagery from a model to the database

        :params model_id
        :params payload
        :returns imagery_id

        :raises DataError
        :returns ID of the prediction
        """

        imagery = Imagery()
        imagery.create(model_id, payload)

        return imagery.id

    @staticmethod
    def delete(model_id: int, imagery_id: int):
        """
        Delete an imagery source by id

        :params model_id
        :params imagery_id
        """

        imagery = Imagery.get(imagery_id)
        imagery.delete()

    @staticmethod
    def patch(model_id: int, imagery_id: int, update: dict) -> int:
        """
        Patch an imagery source by ID
        :params model_id
        :params imagery_id
        :params update
        :returns imagery_id
        """

        imagery = Imagery.get(imagery_id)

        if (imagery):
            imagery.update(update)

            return imagery.id
        else:
            raise ImageryNotFound('Imagery Not Found')

    @staticmethod
    def list(model_id: int):
        """
        Fetch imagery sources for a given model
        :params imagery_id

        :raises ImagerysNotFound
        :returns imagery
        """

        return Imagery.list(model_id)

    @staticmethod
    def get(imagery_id: int):
        """
        Fetch imagery source for a given id
        :params imagery_id

        :raises ImagerysNotFound
        :returns imagery
        """

        imagery = Imagery.get(imagery_id)

        if (imagery):
            return imagery.as_dto().to_primitive()
        else:
            raise ImageryNotFound('Imagery Not Found')

