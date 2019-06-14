from ml_enabler.tests.base import BaseTestCase
from ml_enabler.tests.factories import MLModelFactory, MLModelVersionFactory, \
    PredictionFactory
from ml_enabler.models.ml_model import MLModel, Prediction, MLModelVersion


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


class MLModelVersionTestCase(BaseTestCase):
    def test_latest_version(self):

        # create the model
        ml_model = MLModelFactory()
        self.db.session.add(ml_model)
        self.db.session.commit()

        # create two different versions
        version1 = MLModelVersionFactory(model_id=ml_model.id,
                                         version_major=1,
                                         version_minor=0,
                                         version_patch=0)
        version2 = MLModelVersionFactory(model_id=ml_model.id,
                                         version_major=2,
                                         version_minor=0,
                                         version_patch=0)
        self.db.session.add(version1, version2)
        self.db.session.commit()

        latest_version = MLModelVersion.get_latest_version(ml_model.id).version_major
        assert(latest_version == 2)
