from ml_enabler.tests.base import BaseTestCase
from ml_enabler.tests.factories import MLModelFactory, MLModelVersionFactory, \
    PredictionFactory
from ml_enabler.models.ml_model import MLModel, Prediction


class MLModelTestCase(BaseTestCase):
    def test_create_model(self):
        ml = MLModelFactory(name='this is a test name')
        self.db.session.add(ml)
        self.db.session.commit()
        # print(self.db.session.query(MLModel.name).filter(MLModel.id == 1).all())
        assert self.db.session.query(MLModel).count() == 1


class PredictionTestCase(BaseTestCase):
    def test_create_prediction(self):

        # create the model and a version
        ml_model = MLModelFactory()
        self.db.session.add(ml_model)
        self.db.session.commit()
        version = MLModelVersionFactory(model_id=ml_model.id)
        self.db.session.add(version)
        self.db.session.commit()

        # create the prediction
        prediction = PredictionFactory(model_id=ml_model.id, version_id=version.id)
        self.db.session.add(prediction)
        self.db.session.commit()
        assert self.db.session.query(Prediction).count() == 1
