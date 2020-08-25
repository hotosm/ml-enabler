import maproulette, json
from ml_enabler.models.integration import Integration
from ml_enabler.services.prediction_service import PredictionService
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

        for ele in ['prediction', 'project', 'project_desc', 'challenge', 'challenge_instr', 'threshold', 'inferences']:
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
            project = project_api.create_project(
                data={
                "name": payload.get('project'),
                "display_name": payload.get('project'),
                "description": payload.get('project_desc'),
                "enabled": True
                }
            )

        try:
            challenge = challenge_api.create_challenge(
                data={
                    'name': payload.get('challenge'),
                    'parent': project['data']['id'],
                    'instruction': payload.get('challenge_instr')
                }
            )
        except Exception as e:
            raise e

        req_inferences = payload.get('inferences', 'all')
        req_threshold = float(payload.get('threshold', '0'))

        stream = PredictionService.export(int(payload.get('prediction')))
        inferences = PredictionService.inferences(int(payload.get('prediction')))
        pred = PredictionService.get_prediction_by_id(int(payload.get('prediction')))

        if req_inferences != 'all':
            inferences = [ req_inferences ]

        fc = {
            'type': 'FeatureCollection',
            'features': []
        }

        for row in stream:
            if req_inferences != 'all' and row[3].get(req_inferences) is None:
                continue
            if req_inferences != 'all' and row[3].get(req_inferences) <= req_threshold:
                continue

            properties_dict = {}
            if row[4]:
                properties_dict = row[3]
                valid_dict = {}
                valid_dict.update({'validity': row[4]})
                properties_dict.update(valid_dict)

            feat = {
                "id": row[0],
                "quadkey": row[1],
                "type": "Feature",
                "properties": properties_dict,
                "geometry": json.loads(row[2])
            }

            fc['features'].append(feat)

        challenge_api.add_tasks_to_challenge(
            challenge_id=challenge['data']['id'],
            data=fc
        )

        return {
            "project": project['data']['id'],
            "challenge": challenge['data']['id']
        }

