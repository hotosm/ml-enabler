from ml_enabler.models.integration import Integration
from ml_enabler.models.utils import IntegrationNotFound
from ml_enabler import db

class IntegrationService():
    @staticmethod
    def create(model_id: int,  payload: dict) -> int:
        """
        Validate and add integration from a model to the database

        :params model_id
        :params payload
        :returns integration_id

        :raises DataError
        :returns ID of the prediction
        """

        integration = Integration()
        integration.create(model_id, payload)

        return integration.id

    @staticmethod
    def delete(model_id: int, integration_id: int):
        """
        Delete an integration source by id

        :params model_id
        :params integration_id
        """

        integration = Integration.get(integration_id)
        integration.delete()

    @staticmethod
    def patch(model_id: int, integration_id: int, update: dict) -> int:
        """
        Patch an integration source by ID
        :params model_id
        :params integration_id
        :params update
        :returns integration_id
        """

        integration = Integration.get(integration_id)

        if (integration):
            integration.update(update)

            return integration.id
        else:
            raise IntegrationNotFound('Integration Not Found')

    @staticmethod
    def list(model_id: int):
        """
        Fetch integration sources for a given model
        :params integration_id

        :raises IntegrationNotFound
        :returns integration
        """

        return Integration.list(model_id)

    @staticmethod
    def get(integration_id: int):
        """
        Fetch integration source for a given id
        :params integration_id

        :raises IntegrationNotFound
        :returns integration
        """

        integration = Integration.get(integration_id)

        if (integration):
            return integration.as_dto().to_primitive()
        else:
            raise IntegrationNotFound('Integration Not Found')

