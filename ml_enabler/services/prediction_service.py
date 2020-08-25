import ml_enabler.config as CONFIG
import sqlalchemy
import mercantile, semver
from ml_enabler.models.ml_model import MLModel, PredictionTile, Prediction
from ml_enabler.models.dtos.ml_model_dto import PredictionDTO
from ml_enabler.models.utils import PredictionsNotFound, NotFound, VersionExists
from psycopg2.errors import UniqueViolation
from ml_enabler import db

class PredictionService():
    @staticmethod
    def create(model_id: int, payload: dict) -> int:
        """
        Validate and add predictions from a model to the database
        :params model_id, payload

        :raises DataError
        :returns ID of the prediction
        """

        version = payload['version']
        try:
            semver.VersionInfo.parse(version)
        except Exception as e:
            raise "Version Must be SemVer"

        prediction_dto = PredictionDTO()
        prediction_dto.model_id = model_id
        prediction_dto.version = payload['version']
        prediction_dto.tile_zoom = payload['tileZoom']
        prediction_dto.inf_list = payload['infList']
        prediction_dto.inf_type = payload['infType']
        prediction_dto.inf_binary = payload['infBinary']
        prediction_dto.inf_supertile = payload['infSupertile']
        prediction_dto.validate()

        new_prediction = Prediction()
        try:
            new_prediction.create(prediction_dto)
        except sqlalchemy.exc.IntegrityError as e:
            if isinstance(e.orig, UniqueViolation):
                raise VersionExists
            else:
                raise e

        return new_prediction.id

    @staticmethod
    def export(prediction_id: int):
        prediction = Prediction.get(prediction_id)

        if (prediction):
            stream = prediction.export()

            return stream
        else:
            raise NotFound('Prediction does not exist')

    @staticmethod
    def inferences(prediction_id):
        """
        Get an array of inference names for a given prediction

        :params prediction_id
        :returns list
        """

        return PredictionTile.inferences(prediction_id)


    @staticmethod
    def patch(prediction_id: int, update: dict) -> int:
        """
        Patch a prediction by ID
        :params prediction_id
        :params update
        :returns prediction
        """

        prediction = Prediction.get(prediction_id)

        if (prediction):
            prediction.link(update)

            return prediction_id
        else:
            raise NotFound('Prediction does not exist')

    @staticmethod
    def get_prediction_by_id(prediction_id: int):
        """
        Get a prediction by ID
        :params prediction_id
        :returns prediction
        """

        prediction = Prediction.get(prediction_id)

        if prediction:
            return prediction
        else:
            raise PredictionsNotFound

    @staticmethod
    def get_all_by_model(model_id: int):
        """
        Fetch all predictions of the given model
        :params model_id
        :returns predictions
        :raises PredictionsNotFound
        """
        predictions = Prediction.get_predictions_by_model(model_id)
        prediction_dtos = []
        for prediction in predictions:
            prediction_dtos.append(Prediction.as_dto(prediction).to_primitive())

        return prediction_dtos


class PredictionTileService():
    @staticmethod
    def create(data):
        """
        Bulk inserts prediction tiles
        :params prediction, data
        :returns None
        """

        for prediction in data['predictions']:
            if prediction.get('quadkey_geom') is not None:
                polygon = prediction.get('quadkey_geom')
                bounds = [polygon['coordinates'][0][0][0], polygon['coordinates'][0][0][1], polygon['coordinates'][0][2][0], polygon['coordinates'][0][2][1]]

                prediction["quadkey_geom"] = "SRID=4326;POLYGON(({0} {1},{0} {3},{2} {3},{2} {1},{0} {1}))".format(
                    bounds[0],
                    bounds[1],
                    bounds[2],
                    bounds[3]
                )
            else:
                bounds = mercantile.bounds(mercantile.quadkey_to_tile(prediction.get('quadkey')))
                prediction["quadkey_geom"] = "SRID=4326;POLYGON(({0} {1},{0} {3},{2} {3},{2} {1},{0} {1}))".format(
                    bounds[0],
                    bounds[1],
                    bounds[2],
                    bounds[3]
                )

        connection = db.engine.connect()
        connection.execute(PredictionTile.__table__.insert(), data['predictions'])

    @staticmethod
    def get(predictiontile_id):
        return PredictionTile.get(predictiontile_id)

    @staticmethod
    def validity(predictiontile_id, validity):
        tile = PredictionTile.get(predictiontile_id)
        tile.update(validity)

    @staticmethod
    def mvt(model_id, prediction_id, z, x, y):
        """
        :params model_id
        :params prediction_id
        :params z
        :params x
        :params y
        """

        return PredictionTile.mvt(prediction_id, z, x, y)

    @staticmethod
    def tilejson(model_id, prediction_id):
        """
        Get the TileJSON of the prediction id given

        :params model_id
        :params prediction_id
        :returns dict
        """

        tiles = PredictionTile.count(prediction_id)

        if tiles.count == 0:
            raise PredictionsNotFound('No Prediction Tiles exist')

        ml_model = MLModel.get(model_id)
        prediction = Prediction.get(prediction_id)

        tilejson = {
            "tilejson": "2.1.0",
            "name": ml_model.name,
            "description": ml_model.project_url,
            "inferences": PredictionTile.inferences(prediction_id),
            "token": CONFIG.EnvironmentConfig.MAPBOX_TOKEN,
            "attribution": ml_model.source,
            "version": prediction.version,
            "scheme": "xyz",
            "type": "vector",
            "tiles": [
                "/v1/model/{0}/prediction/{1}/tiles/{{z}}/{{x}}/{{y}}.mvt".format(model_id, prediction_id)
            ],
            "minzoom": 0,
            "maxzoom": prediction.tile_zoom,
            "bounds": PredictionTile.bbox(prediction_id)
        }

        return tilejson
