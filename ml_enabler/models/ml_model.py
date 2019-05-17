from ml_enabler import db
from ml_enabler.models.utils import timestamp


class MLModel(db.Model):
    """ Describes an ML model registered with the service """
    __tablename__ = 'ml_models'

    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, default=timestamp, nullable=False)
    name = db.Column(db.String)
    source = db.Column(db.String)
    dockerhub_url = db.Column(db.String)
    dockethub_hash = db.Column(db.String)

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