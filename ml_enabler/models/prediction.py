from ml_enabler import db
from ml_enabler.models.utils import timestamp
from ml_enabler.models.dtos.ml_model_dto import PredictionDTO

class Prediction(db.Model):
    """ Predictions from a model at a given time """
    __tablename__ = 'predictions'

    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, default=timestamp, nullable=False)
    model_id = db.Column(
        db.BigInteger,
        db.ForeignKey('ml_models.id', name='fk_models'),
        nullable=False
    )

    version = db.Column(db.String, nullable=False)

    docker_url = db.Column(db.String)
    tile_zoom = db.Column(db.Integer, nullable=False)

    log_link = db.Column(db.String)
    model_link =  db.Column(db.String)
    docker_link =  db.Column(db.String)
    save_link = db.Column(db.String)
    tfrecord_link = db.Column(db.String)
    checkpoint_link = db.Column(db.String)
    inf_list = db.Column(db.String)
    inf_type = db.Column(db.String)
    inf_binary = db.Column(db.Boolean)
    inf_supertile = db.Column(db.Boolean)

    def create(self, prediction_dto: PredictionDTO):
        """ Creates and saves the current model to the DB """

        self.model_id = prediction_dto.model_id
        self.version = prediction_dto.version
        self.docker_url = prediction_dto.docker_url
        self.tile_zoom = prediction_dto.tile_zoom
        self.inf_list = prediction_dto.inf_list
        self.inf_type = prediction_dto.inf_type
        self.inf_binary = prediction_dto.inf_binary
        self.inf_supertile = prediction_dto.inf_supertile

        db.session.add(self)
        db.session.commit()

    def link(self, update: dict):
        """ Update prediction to include asset links """

        if update.get("logLink") is not None:
            self.log_link = update["logLink"]
        if update.get("modelLink") is not None:
            self.model_link = update["modelLink"]
        if update.get("dockerLink") is not None:
            self.docker_link = update["dockerLink"]
        if update.get("saveLink") is not None:
            self.save_link = update["saveLink"]
        if update.get("tfrecordLink") is not None:
            self.tfrecord_link = update["tfrecordLink"]
        if update.get("checkpointLink") is not None:
            self.checkpoint_link = update["checkpointLink"]

        db.session.commit()

    def save(self):
        """ Save changes to db"""
        db.session.commit()

    def export(self):
        return db.session.query(
            PredictionTile.id,
            PredictionTile.quadkey,
            ST_AsGeoJSON(PredictionTile.quadkey_geom).label('geometry'),
            PredictionTile.predictions,
            PredictionTile.validity
        ).filter(PredictionTile.prediction_id == self.id).yield_per(100)

    @staticmethod
    def get(prediction_id: int):
        """
        Get prediction with the given ID
        :param prediction_id
        :return prediction if found otherwise None
        """
        query = db.session.query(
            Prediction.id,
            Prediction.created,
            Prediction.docker_url,
            Prediction.model_id,
            Prediction.tile_zoom,
            Prediction.version,
            Prediction.log_link,
            Prediction.model_link,
            Prediction.docker_link,
            Prediction.save_link,
            Prediction.tfrecord_link,
            Prediction.checkpoint_link,
            Prediction.inf_list,
            Prediction.inf_type,
            Prediction.inf_binary,
            Prediction.inf_supertile
        ).filter(Prediction.id == prediction_id)

        return Prediction.query.get(prediction_id)

    @staticmethod
    def get_predictions_by_model(model_id: int):
        """
        Gets predictions for a specified ML Model
        :param model_id: ml model ID in scope
        :return predictions if found otherwise None
        """
        query = db.session.query(
            Prediction.id,
            Prediction.created,
            Prediction.docker_url,
            Prediction.model_id,
            Prediction.tile_zoom,
            Prediction.version,
            Prediction.log_link,
            Prediction.model_link,
            Prediction.docker_link,
            Prediction.save_link,
            Prediction.tfrecord_link,
            Prediction.checkpoint_link,
            Prediction.inf_list,
            Prediction.inf_type,
            Prediction.inf_binary,
            Prediction.inf_supertile
        ).filter(Prediction.model_id == model_id)

        return query.all()

    def delete(self):
        """ Deletes the current model from the DB """
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def as_dto(prediction):
        """ Static method to convert the prediction result as a schematic """

        prediction_dto = PredictionDTO()

        prediction_dto.prediction_id = prediction[0]
        prediction_dto.created = prediction[1]
        prediction_dto.docker_url = prediction[2]
        prediction_dto.model_id = prediction[3]
        prediction_dto.tile_zoom = prediction[4]
        prediction_dto.version = prediction[5]
        prediction_dto.log_link = prediction[6]
        prediction_dto.model_link = prediction[7]
        prediction_dto.docker_link = prediction[8]
        prediction_dto.save_link = prediction[9]
        prediction_dto.tfrecord_link = prediction[10]
        prediction_dto.checkpoint_link = prediction[11]
        prediction_dto.inf_list = prediction[12]
        prediction_dto.inf_type = prediction[13]
        prediction_dto.inf_binary = prediction[14]
        prediction_dto.inf_supertile = prediction[15]

        return prediction_dto

