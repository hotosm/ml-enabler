import json
from ml_enabler.tests.base import BaseTestCase
from ml_enabler.tests.factories import MLModelFactory, MLModelVersionFactory, \
    PredictionFactory
from ml_enabler.models.ml_model import MLModel, Prediction


class StatusTest(BaseTestCase):
    def test_status(self):
        response = self.client.get('/')
        assert(response.get_json() == {'hello': 'world'})


class PredictionAPITest(BaseTestCase):
    def test_no_model(self):
        prediction_payload = {
            "modelId": 1,
            "version": "2.0.0",
            "bbox": [10.013795, 53.5225, 10.048885, 53.540843],
            "tileZoom": 18
        }
        response = self.client.post('model/1/prediction',
                                    data=json.dumps(prediction_payload),
                                    content_type='application/json')
        assert(response.get_json() == {'error': 'model not found'})

    def test_post(self):

        # create a model
        ml_model = MLModelFactory(name='this is a test model')
        self.db.session.add(ml_model)
        self.db.session.commit()

        prediction_payload = {
            "modelId": ml_model.id,
            "version": "2.0.0",
            "bbox": [10.013795, 53.5225, 10.048885, 53.540843],
            "tileZoom": 18
        }
        response = self.client.post(f'model/{ml_model.id}/prediction',
                                    data=json.dumps(prediction_payload),
                                    content_type='application/json')
        assert(response.get_json() == {'prediction_id': ml_model.id})

    def test_get(self):

        # create model
        ml_model = MLModelFactory()
        self.db.session.add(ml_model)
        self.db.session.commit()
        version = MLModelVersionFactory(model_id=ml_model.id)
        self.db.session.add(version)
        self.db.session.commit()

        # create the prediction
        prediction = PredictionFactory(model_id=ml_model.id,
                                       version_id=version.id)
        self.db.session.add(prediction)
        self.db.session.commit()

        response = self.client.get(f'model/{ml_model.id}/prediction?'
                                   'bbox=10.013795,53.5225,'
                                   '10.048885,53.540843')
        assert(len(response.get_json()) == 1)
