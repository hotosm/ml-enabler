import maproulette
from ml_enabler.models.integration import Integration
from ml_enabler.models.utils import IntegrationNotFound
from ml_enabler import db
from urllib.parse import urlparse

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

        if (integration):
            integration.delete()

            return integration.id
        else:
            raise IntegrationNotFound('Integration Not Found')

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

    @staticmethod
    def get_secrets(integration_id: int):
        """
        Fetch integration source for a given id but include auth information (Internal Use Only)
        :params integration_id

        :raises IntegrationNotFound
        :returns integration
        """

        integration = Integration.get_secrets(integration_id)

        if (integration):
            return integration
        else:
            raise IntegrationNotFound('Integration Not Found')

    @staticmethod
    def payload(integration_id: int, payload: dict):
        integration = IntegrationService.get_secrets(integration_id)

        if integration is None:
            raise IntegrationNotFound('Integration Not Found')

        if integration.integration != "maproulette":
            raise Exception("Only MapRoulette Integrations supported");

        for ele in ['project', 'project_desc', 'challenge', 'challenge_instr', 'threshold', 'inferences']:
            if payload.get(ele) is None:
                raise Exception('Missing ' + ele + ' key in body')

        auth = integration.auth
        if payload.get('auth') is not None:
            auth = payload.get('auth')

        parsed = urlparse(integration.url)

        config = maproulette.Configuration(
            api_key=auth,
            hostname=parsed.netloc,
            protocol=parsed.scheme
        )

        project_api = maproulette.Project(config)
        challenge_api = maproulette.Challenge(config)

        try:
            project = project_api.get_project_by_name(
                project_name=payload.get('project')
            )
        except:
            project = project_api.create_project({
                "name": payload.get('project'),
                "display_name": payload.get('project'),
                "description": payload.get('project_desc'),
                "enabled": True
            })

        challenge_api.create_challenge({
            'name': project.get('challenge'),
            'description': project.get('challenge_instr'),
            'enabled': True
        })

