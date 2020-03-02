import ml_enabler.config as CONFIG
from flask_restful import Resource, request, current_app
from ml_enabler.models.dtos.ml_model_dto import MLModelDTO, MLModelVersionDTO
from schematics.exceptions import DataError
from ml_enabler.services.ml_model_service import MLModelService, MLModelVersionService
from ml_enabler.services.prediction_service import PredictionService, PredictionTileService
from ml_enabler.models.utils import NotFound, VersionNotFound, \
    PredictionsNotFound
from ml_enabler.utils import version_to_array, geojson_bounds, bbox_str_to_list, validate_geojson, InvalidGeojson
from sqlalchemy.exc import IntegrityError
import geojson
import boto3
import os

class StatusCheckAPI(Resource):
    """
    Healthcheck method
    ---
    produces:
        - application/json
    responses:
        200:
            description: API status check success
    """

    def get(self):
        return {'hello': 'world'}, 200


class MLModelAPI(Resource):

    def post(self):
        """
        Subscribe a new ML model
        ---
        produces:
            - application/json
        parameters:
            - in: body
              name: body
              required: true
              type: string
              description: JSON object of model information
              schema:
                properties:
                    name:
                        type: string
                        description: name of the ML model
                    source:
                        type: string
                        description: source of the ML model
                    project_url:
                        type: string
                        description: URL to project page
        responses:
            200:
                description: ML Model subscribed
            400:
                description: Invalid Request
            500:
                description: Internal Server Error
        """
        try:
            model_dto = MLModelDTO(request.get_json())
            current_app.logger.info(f'request: {str(request.get_json())}')
            model_dto.validate()
            model_id = MLModelService.subscribe_ml_model(model_dto)
            return {"model_id": model_id}, 200
        except DataError as e:
            current_app.logger.error(f'Error validating request: {str(e)}')
            return str(e), 400
        except IntegrityError as e:
            current_app.logger.error(f'A model with the same name already exists: {str(e)}')
            return str(e), 400

    def delete(self, model_id):
        """
        Deletes an existing model and it's predictions
        ---
        produces:
            - application/json
        parameters:
            - in: path
              name: model_id
              description: ID of the Model to be deleted
              required: true
              type: integer
        responses:
            200:
                description: ML Model deleted
            404:
                description: Model doesn't exist
            500:
                description: Internal Server Error
        """
        try:
            MLModelService.delete_ml_model(model_id)
            return {"success": "model deleted"}, 200
        except NotFound:
            return {"error": "model not found"}, 404
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return {"error": error_msg}

    def get(self, model_id):
        """
        Get model information with the ID
        ---
        produces:
            - application/json
        parameters:
            - in: path
              name: model_id
              description: ID of the Model to be fetched
              required: true
              type: integer
        responses:
            200:
                description: ML Model information
            404:
                description: Model doesn't exist
            500:
                description: Internal Server Error
        """
        try:
            ml_model_dto = MLModelService.get_ml_model_by_id(model_id)
            return ml_model_dto.to_primitive(), 200
        except NotFound:
            return {"error": "model not found"}, 404
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return {"error": error_msg}

    def put(self, model_id):
        """
        Update an existing model
        ---
        produces:
            - application/json
        parameters:
            - in: path
              name: model_id
              description: ID of the Model to update
              required: true
              type: integer
            - in: body
              name: body
              required: true
              type: string
              description: JSON object of model information
              schema:
                properties:
                    name:
                        type: string
                        description: name of the ML model
                    source:
                        type: string
                        description: source of the ML model
                    project_url:
                        type: string
                        description: URL to project page
        responses:
            200:
                description: Updated model information
            404:
                description: Model doesn't exist
            500:
                description: Internal Server Error
        """
        try:
            updated_model_dto = MLModelDTO(request.get_json())
            print(updated_model_dto.to_primitive())
            updated_model_dto.validate()
            model_id = MLModelService.update_ml_model(updated_model_dto)
            return {"model_id": model_id}, 200
        except NotFound:
            return {"error": "model not found"}, 404
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return {"error": error_msg}


class GetAllModels(Resource):
    """ Methods to fetch many ML models """
    def get(self):
        """
        Get all ML models
        ---
        produces:
            - application/json
        responses:
            200:
                description: List of ML models
            404:
                description: No models found
            500:
                description: Internal Server Error
        """
        try:
            ml_models = MLModelService.get_all()
            return ml_models, 200
        except NotFound:
            return {"error": "no models found"}, 404
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return {"error": error_msg}

class PredictionUploadAPI(Resource):
    """ Upload raw ML Models to the platform """

    def post(self, model_id, prediction_id):
        """
        Attach a raw model to a given predition
        ---
        produces:
            - application/json
        responses:
            200:
                description: ID of the prediction
            400:
                description: Invalid Request
            500:
                description: Internal Server Error
        """

        if CONFIG.EnvironmentConfig.ASSET_BUCKET is None:
            return {"error": "Not Configured"}, 501

        key = "{0}/model/{1}/prediction/{2}/model.zip".format(
            CONFIG.EnvironmentConfig.STACK,
            model_id,
            prediction_id
        )

        try:
            boto3.client('s3').head_object(
                Bucket=CONFIG.EnvironmentConfig.ASSET_BUCKET,
                Key=key
            )
        except:
            files = list(request.files.keys())
            if len(files) == 0:
                return {"error": "Model not found in request"}, 400

            model = request.files[files[0]]

            boto3.resource('s3').Bucket(CONFIG.EnvironmentConfig.ASSET_BUCKET).put_object(
                Key=key,
                Body=model.stream
            )

            return { "status": "model uploaded" }, 200
        else:
            return { "error": "model exists" }, 400




class PredictionAPI(Resource):
    """ Methods to manage ML predictions """

    def post(self, model_id):
        """
        Store predictions for an ML Model
        ---
        produces:
            - application/json
        parameters:
            - in: body
              name: body
              required: true
              type: string
              description: JSON object of predictions
              schema:
                properties:
                    modelId:
                        type: integer
                        description: ML Model ID
                        required: true
                    version:
                        type: string
                        description: semver version of the Model
                        required: true
                    docker_url:
                        type: string
                        description: URL to docker image
                        required: false
                    bbox:
                        type: array of floats
                        description: BBOX of the predictions
                        required: true
        responses:
            200:
                description: ID of the prediction
            400:
                description: Invalid Request
            500:
                description: Internal Server Error
        """
        try:
            payload = request.get_json()
            version = payload['version']

            # check if this model exists
            ml_model_dto = MLModelService.get_ml_model_by_id(model_id)

            # check if the version is registered
            model_version = MLModelVersionService.get_version_by_model_version(ml_model_dto.model_id, version)
            prediction_id = PredictionService.create(model_id, model_version.version_id, payload)
            return {"prediction_id": prediction_id}, 200

        except VersionNotFound:
            # if not, add it
            try:
                version_array = version_to_array(version)
                version_dto = MLModelVersionDTO()
                version_dto.model_id = model_id
                version_dto.version_major = version_array[0]
                version_dto.version_minor = version_array[1]
                version_dto.version_patch = version_array[2]
                version_id = MLModelVersionService.create_version(version_dto)

                prediction_id = PredictionService.create(model_id, version_id, payload)
                return {"prediction_id": prediction_id}, 200
            except DataError as e:
                current_app.logger.error(f'Error validating request: {str(e)}')
                return str(e), 400
            except Exception as e:
                error_msg = f'Unhandled error: {str(e)}'
                current_app.logger.error(error_msg)
                return {"error": error_msg}, 500
        except NotFound:
            return {"error": "model not found"}, 404
        except DataError as e:
            current_app.logger.error(f'Error validating request: {str(e)}')
            return str(e), 400
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return {"error": error_msg}, 500

    def get(self, model_id):
        """
        Fetch predictions for a model within supplied bbox
        ---
        produces:
            - application/json
        parameters:
            - in: path
              name: model_id
              description: ID of the Model
              required: true
              type: integer
            - in: query
              name: bbox
              description: bbox in the wsen format. Comma separated floats
              required: true
              type: string
        responses:
            200:
                description: List of all predictions for the model within supplied bbox
            404:
                description: No predictions found
            500:
                description: Internal Server Error
        """
        try:
            bbox = request.args.get('bbox', '')
            if (bbox is None or bbox == ''):
                return {"error": 'A bbox is required'}, 400

            # check if this model exists
            ml_model_dto = MLModelService.get_ml_model_by_id(model_id)

            boundingBox = bbox_str_to_list(bbox)
            predictions = PredictionService.get(ml_model_dto.model_id, boundingBox)
            return predictions, 200
        except PredictionsNotFound:
            return {"error": "Predictions not found"}, 404
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return {"error": error_msg}, 500


class GetAllPredictions(Resource):
    def get(self, model_id):
        """
        Fetch all predictions for a model
        ---
        produces:
            - application/json
        parameters:
            - in: path
              name: model_id
              description: ID of the Model
              required: true
              type: integer
        responses:
            200:
                description: List of all predictions for the model
            404:
                description: No predictions found
            500:
                description: Internal Server Error
        """
        try:
            # check if this model exists
            ml_model_dto = MLModelService.get_ml_model_by_id(model_id)

            predictions = PredictionService.get_all_by_model(ml_model_dto.model_id)
            return predictions, 200
        except PredictionsNotFound:
            return {"error": "Predictions not found"}, 404
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return {"error": error_msg}, 500


class PredictionTileAPI(Resource):
    """
    Methods to manage tile predictions
    """

    def post(self, prediction_id):
        """
        Submit tile level predictions
        ---
        produces:
            - application/json
        parameters:
            - in: body
              name: body
              required: true
              type: string
              description: JSON object of predictions
              schema:
                properties:
                    predictionId:
                        type: integer
                        description: Prediction ID
                        required: true
                    predictions:
                        type: array
                        items:
                            type: object
                            schema:
                                properties:
                                    quadkey:
                                        type: string
                                        description: quadkey of the tile
                                        required: true
                                    centroid:
                                        type: array
                                        items:
                                            type: float
                                        required: true
                                    predictions:
                                        type: object
                                        schema:
                                            properties:
                                                ml_prediction:
                                                    type: float
        responses:
            200:
                description: ID of the prediction
            400:
                description: Invalid Request
            500:
                description: Internal Server Error
        """
        try:
            prediction_dto = PredictionService.get_prediction_by_id(prediction_id)
            data = request.get_json()
            if (len(data['predictions']) == 0):
                return {"error": "Error validating request"}, 400

            PredictionTileService.create(prediction_dto, data)

        except PredictionsNotFound:
            return {"error": "Prediction not found"}, 404
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return {"error": error_msg}, 500


class MLModelWMSAPI(Resource):
    """
    Methods to return raster tiles showing tile based prediction values
    """

    def get(self, model_id, x, y, z):
        """
        Return a raster tile for the given model predictions
        ---
        produces:
            - image/png
        parameters:
            - in: path
              name: model_id
              description: ID of the Model
              required: true
              type: integer
            - in: path
              name: x
              description: X coordinate of the tile
              required: true
              type: integer
            - in: path
              name: y
              description: Y coordinate of the tile
              required: true
              type: integer
            - in: path
              name: z
              description: Z coordinate of the tile
              required: true
              type: integer
        responses:
            200:
                description: Return a tile for the given model
            404:
                description: No predictions found
            500:
                description: Internal Server Error
        """

        return {"error": "NOT IMPLEMENTED"}, 500


class MLModelTilesAPI(Resource):
    """
    Methods to manage prediction tiles at the model level
    """
    def get(self, model_id):
        """
        Get aggregated prediction tile for a model
        within the supplied bbox and tile size
        ---
        produces:
            - application/json
        parameters:
            - in: path
              name: model_id
              description: ID of the Model
              required: true
              type: integer
            - in: query
              name: bbox
              description: bbox in the wsen format. Comma separated floats
              required: true
              type: string
            - in: query
              name: zoom
              description: zoom level for specifying aggregate tile size
              required: true
              type: integer
        responses:
            200:
                description: List of all predictions for the model within supplied bbox
            404:
                description: No predictions found
            500:
                description: Internal Server Error
        """
        try:
            bbox = request.args.get('bbox', '')
            zoom = request.args.get('zoom', '')
            if (bbox is None or bbox == ''):
                return {"error": 'A bbox is required'}, 400

            if (zoom is None or zoom == ''):
                return {"error": 'Zoom level is required for aggregation'}

            # check if this model exists
            ml_model_dto = MLModelService.get_ml_model_by_id(model_id)
            tiles = PredictionTileService.get_aggregated_tiles(
                    ml_model_dto.model_id, bbox, zoom)
            return tiles, 200

        except NotFound:
            return {"error": "Model not found"}, 404
        except PredictionsNotFound:
            return {"error": "No predictions for this bbox"}, 404
        except ValueError as e:
            return {"error": str(e)}, 400
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return {"error": error_msg}, 500


class MLModelTilesGeojsonAPI(Resource):
    """
    Methods to manage prediction tile aggregation for GeoJSON data
    """

    def post(self, model_id: int):
        """
        Aggregate ml predictions for polygons in the supplied GeoJSON
        ---
        produces:
            - application/json
        parameters:
            - in: body
              name: body
              required: true
              type: string
              description: GeoJSON FeatureCollection of Polygons
        responses:
            200:
                description: GeoJSON FeatureCollection with prediction data in properties
            404:
                description: Model not found
            400:
                description: Invalid Request
            500:
                description: Internal Server Error
        """
        try:
            # FIXME - validate the geojson
            data = request.get_json()
            if validate_geojson(data) is False:
                raise InvalidGeojson

            # check if the model exists
            ml_model_dto = MLModelService.get_ml_model_by_id(model_id)

            # get the bbox the geojson
            bbox = geojson_bounds(data)
            prediction_tile_geojson = PredictionTileService.get_aggregated_tiles_geojson(ml_model_dto.model_id, bbox, data)
            return prediction_tile_geojson, 200

        except InvalidGeojson:
            return {"error": "Invalid GeoJSON"}, 400
        except NotFound:
            return {"error": "Model not found"}, 404
        except PredictionsNotFound:
            return {"error": "No predictions for this bbox"}, 404
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return {"error": error_msg}, 500
