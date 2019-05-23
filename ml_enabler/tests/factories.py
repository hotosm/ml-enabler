import factory
import factory.faker
import factory.fuzzy
from factory.alchemy import SQLAlchemyModelFactory
from ml_enabler import db
from ml_enabler.models.ml_model import Prediction, MLModel


class MLModelFactory(SQLAlchemyModelFactory):
    class Meta:
        model = MLModel
        sqlalchemy_session = db.session

    name = factory.faker.Faker('name')
    source = factory.fuzzy.FuzzyText(length=25)
    dockerhub_url = factory.fuzzy.FuzzyText(length=20)
    dockerhub_hash = factory.fuzzy.FuzzyText(length=12)


class PredictionFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Prediction
        sqlalchemy_session = db.session

    title = factory.fuzzy.FuzzyText(length=25)
    body = factory.fuzzy.FuzzyText(length=400)