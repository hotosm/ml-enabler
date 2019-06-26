from ml_enabler.models.ml_model import MLModelVersion, Prediction, PredictionTile
from ml_enabler.models.dtos.ml_model_dto import PredictionDTO
from ml_enabler.models.utils import PredictionsNotFound
from ml_enabler.utils import bbox_str_to_list, bbox_to_quadkeys, tuple_to_dict, polygon_to_wkt, geojson_to_bbox
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
        :params prediction_id
        :returns prediction
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
            prediction_dto = Prediction.as_dto(prediction)
            data.append(prediction_dto.to_primitive())

        return data

    @staticmethod
    def get_all_by_model(model_id: int):
        """
        Fetch all predictions of the given model
        :params model_id
        :returns predictions
        :raises PredictionsNotFound
        """
        predictions = Prediction.get_predictions_by_model(model_id)
        print(predictions)
        prediction_dtos = []
        for prediction in predictions:
            print(prediction)
            prediction_dtos.append(Prediction.as_dto(prediction).to_primitive())

        return prediction_dtos


class PredictionTileService():
    @staticmethod
    def create(prediction: PredictionDTO, data):
        """
        Bulk inserts prediction tiles
        :params prediction, data
        :returns None
        """
        connection = db.engine.connect()
        connection.execute(PredictionTile.__table__.insert(), data['predictions'])

    @staticmethod
    def get_aggregated_tiles(model_id: int, bbox: list, zoom: int):
        """
        Get aggregated predictions at the specified zoom level for the supplied bbox
        :params model_id, bbox, zoom
        :returns list of tiles with predictions
        """
        # get predictions within this bbox
        boundingBox = bbox_str_to_list(bbox)
        predictions = PredictionService.get(model_id, boundingBox, latest=True)
        # find quadkeys for the given bbox
        boundingBox = bbox_str_to_list(bbox)
        quadkeys = bbox_to_quadkeys(boundingBox, zoom)
        prediction_tiles = {}
        for prediction in predictions:
            # query all tiles within those quadkeys and aggregate
            if int(prediction['tileZoom']) < int(zoom):
                raise ValueError('Aggregate zoom level is greater than prediction zoom')

            tiles = list(map(tuple_to_dict, PredictionTile.get_tiles_by_quadkey
                         (prediction['predictionsId'], tuple(quadkeys), zoom)))
            prediction_tiles[prediction['predictionsId']] = tiles

        return prediction_tiles

    @staticmethod
    def get_aggregated_tiles_geojson(model_id: int, bbox: list, geojson: dict):
        """
        For the given geojson, find predictions for each polygon and return the geojson
        :param model_id, bbox, geojson
        :returns geojson
        """
        # get the latest prediction
        prediction = PredictionService.get(model_id, bbox, latest=True)
        # for each geojson feature, find the tiles and aggregate
        for feature in geojson['features']:
            tile_aggregate = PredictionTile.get_aggregate_for_polygon(prediction[0]['predictionsId'], polygon_to_wkt(feature['geometry']))
            if (len(tile_aggregate) > 0):
                feature['properties']['ml_prediction'] = tile_aggregate[0]
                feature['properties']['osm_building_area'] = tile_aggregate[1]

        return geojson
