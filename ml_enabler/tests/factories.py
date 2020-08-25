import factory
import factory.faker
import factory.fuzzy
from factory.alchemy import SQLAlchemyModelFactory
from ml_enabler import db
from ml_enabler.models.ml_model import Prediction, MLModel, \
    MLModelVersion


class MLModelFactory(SQLAlchemyModelFactory):
    class Meta:
        model = MLModel
        sqlalchemy_session = db.session

    name = factory.faker.Faker('name')
    source = factory.fuzzy.FuzzyText(length=25)
    project_url = factory.fuzzy.FuzzyText(length=20)


class MLModelVersionFactory(SQLAlchemyModelFactory):
    class Meta:
        model = MLModelVersion
        sqlalchemy_session = db.session

    version_major = factory.fuzzy.FuzzyInteger(0)
    version_minor = factory.fuzzy.FuzzyInteger(0)
    version_patch = factory.fuzzy.FuzzyInteger(0)


class PredictionFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Prediction
        sqlalchemy_session = db.session

    docker_url = factory.fuzzy.FuzzyText(length=25)
    bbox = 'SRID=4326;POLYGON((10.048885 53.5225,10.048885 53.540843,10.013795 53.540843,10.013795 53.5225,10.048885 53.5225))'
    tile_zoom = 18
