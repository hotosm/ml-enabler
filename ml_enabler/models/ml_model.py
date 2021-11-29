import mercantile
import json
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.ext.mutable import MutableDict, MutableList
from ml_enabler import db
from ml_enabler.models.utils import timestamp
from geoalchemy2 import Geometry
from geoalchemy2.functions import ST_Envelope, ST_AsGeoJSON, ST_Within, \
     ST_GeomFromText, ST_Intersects, ST_MakeEnvelope
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import func, text
from sqlalchemy.sql.expression import cast
import sqlalchemy
from flask_login import UserMixin
from ml_enabler.models.dtos.ml_model_dto import MLModelDTO, PredictionDTO

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True)
    password = db.Column(db.String)
    name = db.Column(db.String)

    def password_check(self, test):
        results = db.session.execute(text('''
             SELECT
                password = crypt(:test, password)
            FROM
                users
            WHERE
                id = :uid
        '''), {
            'test': test,
            'uid': self.id
        }).fetchall()

        return results[0][0]

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


class PredictionTile(db.Model):
    """ Store individual tile predictions """
    __tablename__ = 'prediction_tiles'

    id = db.Column(db.Integer, primary_key=True)

    prediction_id = db.Column(
        db.BigInteger,
        db.ForeignKey('predictions.id', name='fk_predictions'),
        nullable=False
    )

    quadkey = db.Column(db.String, nullable=False)
    quadkey_geom = db.Column(Geometry('POLYGON', srid=4326), nullable=False)
    centroid = db.Column(Geometry('POINT', srid=4326))
    predictions = db.Column(postgresql.JSONB, nullable=False)
    validity = db.Column(MutableDict.as_mutable(postgresql.JSONB), nullable=True)

    prediction_tiles_quadkey_idx = db.Index(
        'prediction_tiles_quadkey_idx',
        'prediction_tiles.quadkey',
        postgresql_ops={ 'quadkey': 'text_pattern_ops' }
    )

    @staticmethod
    def get(predictiontile_id: int):

        query = db.session.query(
            PredictionTile.id,
            PredictionTile.prediction_id,
            PredictionTile.validity,
        ).filter(PredictionTile.id == predictiontile_id)

        return PredictionTile.query.get(predictiontile_id)

    def update(self, validity):
        self.validity = validity

        db.session.commit()

    @staticmethod
    def inferences(prediction_id: int):
        results = db.session.execute(text('''
             SELECT
                DISTINCT jsonb_object_keys(predictions)
            FROM
                prediction_tiles
            WHERE
                prediction_id = :pred
        '''), {
            'pred': prediction_id
        }).fetchall()

        inferences = []
        for res in results:
            inferences.append(res[0])

        return inferences

    @staticmethod
    def count(prediction_id: int):
        return db.session.query(
            func.count(PredictionTile.quadkey).label("count")
        ).filter(PredictionTile.prediction_id == prediction_id).one()

    @staticmethod
    def bbox(prediction_id: int):
        result = db.session.execute(text('''
            SELECT
                ST_Extent(quadkey_geom)
            FROM
                prediction_tiles
            WHERE
                prediction_id = :pred
        '''), {
            'pred': prediction_id
        }).fetchone()

        bbox = []
        for corners in result[0].replace('BOX(', '').replace(')', '').split(' '):
            for corner in corners.split(','):
                bbox.append(float(corner))

        return bbox

    def mvt(prediction_id: int, z: int, x: int, y: int):
        grid = mercantile.xy_bounds(x, y, z)

        result = db.session.execute(text('''
            SELECT
                ST_AsMVT(q, 'data', 4096, 'geom', 'id') AS mvt
            FROM (
                SELECT
                    p.id AS id,
                    quadkey AS quadkey,
                    predictions || COALESCE(v.validity, '{}'::JSONB) AS props,
                    ST_AsMVTGeom(quadkey_geom, ST_Transform(ST_MakeEnvelope(:minx, :miny, :maxx, :maxy, 3857), 4326), 4096, 256, false) AS geom
                FROM
                    prediction_tiles AS p
                    LEFT JOIN (
                        SELECT
                            id,
                            JSONB_Object_Agg('v_'||key, value) AS validity
                        FROM
                            prediction_tiles,
                            jsonb_each(validity)
                        GROUP BY
                            id
                    ) AS v ON p.id = v.id
                WHERE
                    p.prediction_id = :pred
                    AND ST_Intersects(p.quadkey_geom, ST_Transform(ST_MakeEnvelope(:minx, :miny, :maxx, :maxy, 3857), 4326))
            ) q
        '''), {
            'pred': prediction_id,
            'minx': grid[0],
            'miny': grid[1],
            'maxx': grid[2],
            'maxy': grid[3]
        }).fetchone()

        return bytes(result.values()[0])

    @staticmethod
    def get_tiles_by_quadkey(prediction_id: int, quadkeys: tuple, zoom: int):
        return db.session.query(
            func.substr(PredictionTile.quadkey, 1, zoom).label('qaudkey'),
            func.avg(cast(cast(PredictionTile.predictions['ml_prediction'], sqlalchemy.String), sqlalchemy.Float)).label('ml_prediction'),
            func.avg(cast(cast(PredictionTile.predictions['osm_building_area'], sqlalchemy.String), sqlalchemy.Float)).label('osm_building_area')
        ).filter(PredictionTile.prediction_id == prediction_id).filter(func.substr(PredictionTile.quadkey, 1, zoom).in_(quadkeys)).group_by(func.substr(PredictionTile.quadkey, 1, zoom)).all()

    @staticmethod
    def get_aggregate_for_polygon(prediction_id: int, polygon: str):
        return db.session.query(
            func.avg(cast(cast(PredictionTile.predictions['ml_prediction'], sqlalchemy.String), sqlalchemy.Float)).label('ml_prediction'),
            func.avg(cast(cast(PredictionTile.predictions['osm_building_area'], sqlalchemy.String), sqlalchemy.Float)).label('osm_building_area')
        ).filter(PredictionTile.prediction_id == prediction_id).filter(ST_Within(PredictionTile.centroid, ST_GeomFromText(polygon)) == 'True').one()

class MLModel(db.Model):
    """ Describes an ML model registered with the service """
    __tablename__ = 'ml_models'

    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, default=timestamp, nullable=False)
    tags = db.Column(MutableList.as_mutable(postgresql.JSONB), nullable=False)
    name = db.Column(db.String, unique=True)
    source = db.Column(db.String)
    archived = db.Column(db.Boolean)
    project_url = db.Column(db.String)
    predictions = db.relationship(
        Prediction,
        backref='ml_models',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    def create(self, ml_model_dto: MLModelDTO):
        """ Creates and saves the current model to the DB """

        self.name = ml_model_dto.name
        self.source = ml_model_dto.source
        self.archived = False
        self.tags = ml_model_dto.tags
        self.project_url = ml_model_dto.project_url

        db.session.add(self)
        db.session.commit()
        return self

    def save(self):
        """ Save changes to db"""
        db.session.commit()

    @staticmethod
    def get(model_id: int):
        """
        Gets specified ML Model
        :param model_id: ml model ID in scope
        :return ML Model if found otherwise None
        """
        return MLModel.query.get(model_id)

    @staticmethod
    def get_all(model_filter: str, model_archived: bool):
        """
        Get all models in the database
        """
        return MLModel.query.filter(
            MLModel.name.ilike(model_filter + '%'),
            MLModel.archived == model_archived
        ).all()

    def delete(self):
        """ Deletes the current model from the DB """
        db.session.delete(self)
        db.session.commit()

    def as_dto(self):
        """
        Convert the model to it's dto
        """
        model_dto = MLModelDTO()
        model_dto.model_id = self.id
        model_dto.name = self.name
        model_dto.tags = self.tags
        model_dto.created = self.created
        model_dto.source = self.source
        model_dto.archived = self.archived
        model_dto.project_url = self.project_url

        return model_dto

    def update(self, updated_ml_model_dto: MLModelDTO):
        """ Updates an ML model """
        self.id = updated_ml_model_dto.model_id
        self.name = updated_ml_model_dto.name
        self.source = updated_ml_model_dto.source
        self.project_url = updated_ml_model_dto.project_url
        self.archived = updated_ml_model_dto.archived
        self.tags = updated_ml_model_dto.tags

        db.session.commit()

