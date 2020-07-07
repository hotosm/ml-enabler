import mercantile
import json
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.ext.mutable import MutableDict
from ml_enabler import db
from ml_enabler.models.utils import timestamp
from ml_enabler.utils import bbox_to_polygon_wkt, geojson_to_bbox
from geoalchemy2 import Geometry
from geoalchemy2.functions import ST_Envelope, ST_AsGeoJSON, ST_Within, \
     ST_GeomFromText, ST_Intersects, ST_MakeEnvelope
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import func, text
from sqlalchemy.sql.expression import cast
import sqlalchemy
from ml_enabler.models.dtos.ml_model_dto import MLModelDTO, \
    MLModelVersionDTO, PredictionDTO

class Imagery(db.Model):
    """ Store an imagery source for a given model """
    __tablename__ = 'imagery'

    id = db.Column(db.Integer, primary_key=True)

    model_id = db.Column(
        db.BigInteger,
        db.ForeignKey('ml_models.id', name='fk_models'),
        nullable=False
    )

    name = db.Column(db.String, nullable=False)
    url =  db.Column(db.String, nullable=False)

    def create(self, model_id: int, imagery: dict):
        """ Creates and saves the current model to the DB """

        self.model_id = model_id
        self.name = imagery.get("name")
        self.url = imagery.get("url")

        db.session.add(self)
        db.session.commit()

        return self

    def get(imagery_id: int):
        query = db.session.query(
            Imagery.id,
            Imagery.name,
            Imagery.url,
            Imagery.model_id
        ).filter(Imagery.id == imagery_id)

        return Imagery.query.get(imagery_id)

    def delete(self):
        """ Deletes the current model from the DB """
        db.session.delete(self)
        db.session.commit()

    def list(model_id: int):
        query = db.session.query(
            Imagery.id,
            Imagery.name,
            Imagery.url
        ).filter(Imagery.model_id == model_id)

        imagery = []
        for img in query.all():
            imagery.append({
                "id": img[0],
                "name": img[1],
                "url": img[2]
            })

        return imagery

    def update(self, update: dict):
        if update.get("name") is not None:
            self.name = update["name"]
        if update.get("url") is not None:
            self.url = update["url"]

        db.session.commit()

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

    version_id = db.Column(
        db.Integer,
        db.ForeignKey('ml_model_versions.id', name='ml_model_versions_fk'),
        nullable=False
    )

    docker_url = db.Column(db.String)
    bbox = db.Column(Geometry('POLYGON', srid=4326))
    tile_zoom = db.Column(db.Integer, nullable=False)

    log_link = db.Column(db.String)
    model_link =  db.Column(db.String)
    docker_link =  db.Column(db.String)
    save_link = db.Column(db.String)
    inf_list = db.Column(db.String)
    inf_type = db.Column(db.String)
    inf_binary = db.Column(db.Boolean) #should this be String? 

    def create(self, prediction_dto: PredictionDTO):
        """ Creates and saves the current model to the DB """

        self.model_id = prediction_dto.model_id
        self.version_id = prediction_dto.version_id
        self.docker_url = prediction_dto.docker_url
        self.bbox = ST_GeomFromText(bbox_to_polygon_wkt(prediction_dto.bbox), 4326)
        self.tile_zoom = prediction_dto.tile_zoom
        self.inf_list = prediction_dto.inf_list
        self.inf_type = prediction_dto.inf_type
        self.inf_binary = prediction_dto.inf_binary

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
            ST_AsGeoJSON(ST_Envelope(Prediction.bbox)).label('bbox'),
            Prediction.model_id,
            Prediction.tile_zoom,
            Prediction.version_id,
            Prediction.inf_list,
            Prediction.inf_type, 
            Prediction.inf_binary
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
            ST_AsGeoJSON(ST_Envelope(Prediction.bbox)).label('bbox'),
            Prediction.model_id,
            Prediction.tile_zoom,
            Prediction.version_id,
            Prediction.log_link,
            Prediction.model_link,
            Prediction.docker_link,
            Prediction.save_link,
            Prediction.inf_list,
            Prediction.inf_type, 
            Prediction.inf_binary
        ).filter(Prediction.model_id == model_id)

        return query.all()

    @staticmethod
    def get_latest_predictions_in_bbox(model_id: int, version_id: int, bbox: list):
        """
        Fetch latest predictions for the specified model intersecting
        the given bbox

        :param model_id, version_id, bbox
        :return list of predictions
        """
        query = db.session.query(
            Prediction.id,
            Prediction.created,
            Prediction.docker_url,
            ST_AsGeoJSON(ST_Envelope(Prediction.bbox)).label('bbox'), Prediction.model_id, Prediction.tile_zoom, Prediction.version_id
        ).filter(Prediction.model_id == model_id).filter(Prediction.version_id == version_id).filter(ST_Intersects(Prediction.bbox, ST_MakeEnvelope(bbox[0], bbox[1], bbox[2], bbox[3], 4326))).order_by(Prediction.created.desc()).limit(1)

        return query.all()

    def get_all_predictions_in_bbox(model_id: int, bbox: list):
        """
        Fetch all predictions for the specified model intersecting the given
        bbox
        :param model_id, bbox
        :return list of predictions
        """
        query = db.session.query(
            Prediction.id,
            Prediction.created,
            Prediction.docker_url,
            ST_AsGeoJSON(ST_Envelope(Prediction.bbox)).label('bbox'), Prediction.model_id, Prediction.tile_zoom, Prediction.version_id
        ).filter(Prediction.model_id == model_id).filter(ST_Intersects(Prediction.bbox, ST_MakeEnvelope(bbox[0], bbox[1], bbox[2], bbox[3], 4326)))

        return query.all()

    def delete(self):
        """ Deletes the current model from the DB """
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def as_dto(prediction):
        """ Static method to convert the prediction result as a schematic """

        prediction_dto = PredictionDTO()
        version = MLModelVersion.get(prediction[6])

        version_dto = version.as_dto()

        prediction_dto.prediction_id = prediction[0]
        prediction_dto.created = prediction[1]
        prediction_dto.docker_url = prediction[2]
        prediction_dto.bbox = geojson_to_bbox(prediction[3])
        prediction_dto.model_id = prediction[4]
        prediction_dto.tile_zoom = prediction[5]
        prediction_dto.version_id = prediction[6]
        prediction_dto.version_string = f'{version_dto.version_major}.{version_dto.version_minor}.{version_dto.version_patch}'

        prediction_dto.log_link = prediction[7]
        prediction_dto.model_link = prediction[8]
        prediction_dto.docker_link = prediction[9]
        prediction_dto.save_link = prediction[10]
        prediction_dto.inf_list = prediction[11]
        prediction_dto.inf_type = prediction[12]
        prediction_dto.inf_binary = prediction[13]

        return prediction_dto


class MLModel(db.Model):
    """ Describes an ML model registered with the service """
    __tablename__ = 'ml_models'

    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, default=timestamp, nullable=False)
    name = db.Column(db.String, unique=True)
    source = db.Column(db.String)
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
    def get_all():
        """
        Get all models in the database
        """
        return MLModel.query.all()

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
        model_dto.created = self.created
        model_dto.source = self.source
        model_dto.project_url = self.project_url

        return model_dto

    def update(self, updated_ml_model_dto: MLModelDTO):
        """ Updates an ML model """
        self.id = updated_ml_model_dto.model_id
        self.name = updated_ml_model_dto.name
        self.source = updated_ml_model_dto.source
        self.project_url = updated_ml_model_dto.project_url

        db.session.commit()


class MLModelVersion(db.Model):
    """ Stores versions of all subscribed ML Models """
    __tablename__ = 'ml_model_versions'

    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, default=timestamp, nullable=False)
    model_id = db.Column(db.BigInteger, db.ForeignKey(
        'ml_models.id', name='fk_models_versions'), nullable=False)
    version_major = db.Column(db.Integer, nullable=False)
    version_minor = db.Column(db.Integer, nullable=False)
    version_patch = db.Column(db.Integer, nullable=False)

    def create(self, version_dto: MLModelVersionDTO):
        """  Creates a new version of an ML model """

        self.model_id = version_dto.model_id
        self.version_major = version_dto.version_major
        self.version_minor = version_dto.version_minor
        self.version_patch = version_dto.version_patch

        db.session.add(self)
        db.session.commit()
        return self

    def save(self):
        """ Save changes to the db """
        db.session.commit()

    @staticmethod
    def get(version_id: int):
        """
        Get a version using the id
        :param version_id
        :return version or None
        """
        return MLModelVersion.query.get(version_id)

    @staticmethod
    def get_version(model_id: int, version_major: int, version_minor: int, version_patch: int):
        """
        Get a version object for the supplied and corresponding semver
        :param model_id, version_major, version_minor, version_patch
        :return version or None
        """
        return MLModelVersion.query.filter_by(model_id=model_id, version_major=version_major, version_minor=version_minor, version_patch=version_patch).one()

    @staticmethod
    def get_latest_version(model_id: int):
        """
        Get the latest version of a given model
        :param model_id
        :return version or None
        """
        return MLModelVersion.query.filter_by(model_id=model_id).order_by(MLModelVersion.version_major.desc(), MLModelVersion.version_minor.desc(),
                                                                          MLModelVersion.version_patch.desc()).first()

    def as_dto(self):
        """
        Convert the version object to it's DTO
        """
        version_dto = MLModelVersionDTO()
        version_dto.version_id = self.id
        version_dto.model_id = self.model_id
        version_dto.created = self.created
        version_dto.version_major = self.version_major
        version_dto.version_minor = self.version_minor
        version_dto.version_patch = self.version_patch

        return version_dto
