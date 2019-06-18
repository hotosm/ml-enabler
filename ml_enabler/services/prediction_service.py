from flask import current_app
from ml_enabler.models.ml_model import MLModel, MLModelVersion, Prediction, PredictionTile
from ml_enabler.models.dtos.ml_model_dto import MLModelDTO, MLModelVersionDTO, PredictionDTO
from ml_enabler.models.utils import NotFound, VersionNotFound, \
    PredictionsNotFound
from ml_enabler.utils import bbox_to_quadkeys, tuple_to_dict, \
    polygon_to_wkt, geojson_to_bbox, version_to_array, bbox_str_to_list
from ml_enabler import db


class PredictionService():
    @staticmethod
    def create(model_id: int, version_id: int, payload: dict) -> int:
        """
        Validate and add predictions from a model to the database
        :params model_id, version_id, payload

        :raises DataError
        :returns ID of the prediction
        """

        prediction_dto = PredictionDTO()
        prediction_dto.model_id = model_id
        prediction_dto.version_id = version_id
        prediction_dto.bbox = payload['bbox']
        prediction_dto.tile_zoom = payload['tileZoom']
        prediction_dto.validate()

        new_prediction = Prediction()
        new_prediction.create(prediction_dto)
        return new_prediction.id

    @staticmethod
    def get_prediction_by_id(prediction_id: int):
        """
        Get a prediction by ID
        """

        prediction = Prediction.get(prediction_id)
        if prediction:
            return Prediction.as_dto(prediction)
        else:
            raise PredictionsNotFound

    @staticmethod
    def get(model_id: int, bbox: list, latest=False):
        """
        Fetch latest predictions from a model for the given bbox
        :params model_id, bbox

        :raises PredictionsNotFound
        :returns predictions
        """

        if (latest):
            # get the latest version
            latest_version = MLModelVersion.get_latest_version(model_id)
            if (latest_version is None):
                raise PredictionsNotFound('Predictions not found')
            else:
                version_id = latest_version.id
                predictions = Prediction.get_latest_predictions_in_bbox(model_id, version_id, bbox)
        else:
            predictions = Prediction.get_all_predictions_in_bbox(model_id, bbox)

        if (len(predictions) == 0):
            raise PredictionsNotFound('Predictions not found')

        data = []
        for prediction in predictions:
            prediction_dto = PredictionDTO()
            version = MLModelVersion.get(prediction[6])
            version_dto = version.as_dto()

            prediction_dto.prediction_id = prediction[0]
            prediction_dto.created = prediction[1]
            prediction_dto.dockerhub_hash = prediction[2]
            prediction_dto.bbox = geojson_to_bbox(prediction[3])
            prediction_dto.model_id = prediction[4]
            prediction_dto.tile_zoom = prediction[5]
            prediction_dto.version_id = prediction[6]
            prediction_dto.version_string = f'{version_dto.version_major}.{version_dto.version_minor}.{version_dto.version_patch}'

            data.append(prediction_dto.to_primitive())

        return data


class PredictionTileService():
    @staticmethod
    def create(prediction: PredictionDTO, data):
        connection = db.engine.connect()
        connection.execute(PredictionTile.__table__.insert(), data['predictions'])

    @staticmethod
    def get_aggregated_tiles(model_id: int, bbox: list, zoom: int):
        # get predictions within this bbox
        boundingBox = bbox_str_to_list(bbox)
        predictions = PredictionService.get(model_id, boundingBox, latest=True)
        print(predictions)
        # find quadkeys for the given bbox
        boundingBox = bbox_str_to_list(bbox)
        quadkeys = bbox_to_quadkeys(boundingBox, zoom)
        prediction_tiles = {}
        for prediction in predictions:
            # query all tiles within those quadkeys and aggregate
            tiles = list(map(tuple_to_dict, PredictionTile.get_tiles_by_quadkey
                         (prediction['predictionsId'], tuple(quadkeys), zoom)))
            prediction_tiles[prediction['predictionsId']] = tiles

        return prediction_tiles

    @staticmethod
    def get_aggregated_tiles_geojson(model_id: int, bbox: list, geojson: dict):

        # and get the latest prediction
        prediction = PredictionService.get(model_id, bbox, latest=True)
        # for each geojson feature, find the tiles and aggregate
        for feature in geojson['features']:
            tile_aggregate = PredictionTile.get_aggregate_for_polygon(prediction[0]['predictionsId'], polygon_to_wkt(feature['geometry']))
            if (len(tile_aggregate) > 0):
                feature['properties']['ml_prediction'] = tile_aggregate[0]

        return geojson
