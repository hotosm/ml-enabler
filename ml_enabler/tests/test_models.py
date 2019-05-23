from ml_enabler.tests.base import BaseTestCase
from ml_enabler.tests.factories import MLModelFactory
from ml_enabler.models.ml_model import MLModel
from ml_enabler import db

class MLModelTestCase(BaseTestCase):
    def test_create_model(self):
        ml = MLModelFactory()
        self.db.session.add(ml)
        self.db.session.commit()
        assert self.db.session.query(MLModel).count() == 1