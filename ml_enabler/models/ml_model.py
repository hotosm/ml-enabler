from ml_enabler import db
from ml_enabler.models.utils import timestamp
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql


class Prediction(db.Model):
    """ Predictions from a model at a given time """
    __tablename__ = 'predictions'

    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, default=timestamp, nullable=False)
    model_id = db.Column(db.BigInteger, db.ForeignKey(
                        'ml_models.id', name='fk_models'), nullable=False)
    version = db.Column(db.Integer, nullable=False)
    bbox = db.Column(Geometry('MULTIPOLYGON', srid=4326))
    predictions = db.Column(postgresql.JSONB, nullable=False)

    def create(self):
        """ Creates and saves the current model to the DB """
        db.session.add(self)
        db.session.commit()

    def save(self):
        """ Save changes to db"""
        db.session.commit()

    @staticmethod
    def get_predictions_by_model(model_id: int):
        """
        Gets predictions for a specified ML Model
        :param model_id: ml model ID in scope
        :return: predictions if found otherwise None
        """
        return Prediction.query.filter_by(model_id=model_id)

    def delete(self):
        """ Deletes the current model from the DB """
        db.session.delete(self)
        db.session.commit()


class MLModel(db.Model):
    """ Describes an ML model registered with the service """
    __tablename__ = 'ml_models'

    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, default=timestamp, nullable=False)
    name = db.Column(db.String)
    source = db.Column(db.String)
    dockerhub_url = db.Column(db.String)
    dockerhub_hash = db.Column(db.String)
    predictions = db.relationship(Prediction, backref='ml_models',
                                  cascade='all, delete-orphan', lazy='dynamic')

    def create(self):
        """ Creates and saves the current model to the DB """
        db.session.add(self)
        db.session.commit()

    def save(self):
        """ Save changes to db"""
        db.session.commit()

    @staticmethod
    def get(model_id: int):
        """
        Gets specified ML Model
        :param model_id: ml model ID in scope
        :return: ML Model if found otherwise None
        """
        return MLModel.query.get(model_id)

    def delete(self):
        """ Deletes the current model from the DB """
        db.session.delete(self)
        db.session.commit()
