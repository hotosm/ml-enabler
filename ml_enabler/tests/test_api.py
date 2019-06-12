import json
from ml_enabler.tests.base import BaseTestCase
from ml_enabler.tests.factories import MLModelFactory, MLModelVersionFactory, \
    PredictionFactory
from ml_enabler.models.ml_model import MLModel, Prediction


class StatusTest(BaseTestCase):
    def test_status(self):
        response = self.client.get('/')
        assert(response.get_json() == {'hello': 'world'})


class PredictionPostAPITest(BaseTestCase):
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
        ml = MLModelFactory(name='this is a test model')
        self.db.session.add(ml)
        self.db.session.commit()

        prediction_payload = {
            "modelId": 1,
            "version": "2.0.0",
            "bbox": [10.013795, 53.5225, 10.048885, 53.540843],
            "tileZoom": 18
        }
        response = self.client.post('model/1/prediction',
                                    data=json.dumps(prediction_payload),
                                    content_type='application/json')
        assert(response.get_json() == {'prediction_id': 1})
