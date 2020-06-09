import ml_enabler.config as CONFIG
import io, os, pyproj, json, csv, geojson, boto3
from tiletanic import tilecover, tileschemes
from shapely.geometry import shape
from shapely.ops import transform
from functools import partial
from flask import make_response
from flask_restful import Resource, request, current_app
from flask import Response
from ml_enabler.models.dtos.ml_model_dto import MLModelDTO, MLModelVersionDTO, PredictionDTO
from schematics.exceptions import DataError
from ml_enabler.services.ml_model_service import MLModelService, MLModelVersionService
from ml_enabler.models.ml_model import MLModelVersion
from ml_enabler.services.prediction_service import PredictionService, PredictionTileService
from ml_enabler.services.imagery_service import ImageryService
from ml_enabler.models.utils import NotFound, VersionNotFound, \
    PredictionsNotFound, ImageryNotFound
from ml_enabler.utils import version_to_array, geojson_bounds, bbox_str_to_list, validate_geojson, InvalidGeojson
from sqlalchemy.exc import IntegrityError

class MetaAPI(Resource):
    """
    Return metadata about the API
    """
    def get(self):
        return {
            'version': 1,
            'environment': CONFIG.EnvironmentConfig.ENVIRONMENT
        }, 200

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

class MapboxAPI(Resource):
    def get(self):
        return {
            "token": CONFIG.EnvironmentConfig.MAPBOX_TOKEN
        }, 200

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
            return {
                "status": 404,
                "error": "model not found"
            }, 404
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return {
                "status": 500,
                "error": error_msg
            }, 500

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
            return {
                "status": 404,
                "error": "model not found"
            }, 404
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return {
                "status": 500,
                "error": error_msg
            }, 500

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
            return {
                "status": 404,
                "error": "model not found"
            }, 404
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return {
                "status": 500,
                "error": error_msg
            }, 500

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
            return {
                "status": 404,
                "error": "no models found"
            }, 404
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return {
                "status": 500,
                "error": error_msg
            }, 500

class ImageryAPI(Resource):
    """ Upload imagery sources for a given model """

    def delete(self, model_id, imagery_id):
        """
        Delete an imagery source
        ---
        produces:
            - application/json
        parameters:
            - in: path
              name: model_id
              description: ID of the Model
              required: true
              type: integer
            - in: path
              name: imagery_id
              description: ID of the Imagery Source
              required: true
              type: integer
        responses:
            200:
                description: ID of the imagery source
        """

        ImageryService.delete(model_id, imagery_id)

        return "deleted", 200

    def patch(self, model_id, imagery_id):
        """
        Update an existing imagery source
        ---
        produces:
            - application/json
        parameters:
            - in: path
              name: model_id
              description: ID of the Model
              required: true
            - in: path
              name: imagery_id
              description: ID of the Imagery Source
              required: true
              type: integer             type: integer
        responses:
            200:
                description: ID of the imagery source
        """
        imagery = request.get_json();
        imagery_id = ImageryService.patch(model_id, imagery_id, imagery)

        return {
            "model_id": model_id,
            "imagery_id": imagery_id
        }, 200


    def post(self, model_id):
        """
        Create a new imagery source
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
                description: ID of the imagery source
        """
        try:
            imagery = request.get_json()
            imagery_id = ImageryService.create(model_id, imagery)

            return {
                "model_id": model_id,
                "imagery_id": imagery_id
            }, 200
        except Exception as e:
            error_msg = f'Imagery Post: {str(e)}'
            current_app.logger.error(error_msg)
            return {
                "status": 500,
                "error": "Failed to save imagery source to DB"
            }, 500

    def get(self, model_id):
        """
        Fetch all imagery for the given model
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
                description: All imagery for the given model
            500:
                description: Internal Server Error
        """
        try:
            imagery = ImageryService.list(model_id)
            return imagery, 200
        except ImageryNotFound:
            return {
                "status": 404,
                "error": "Imagery not found"
            }, 404
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return {
                "status": 500,
                "error": error_msg
            }, 500

class PredictionExport(Resource):
    """ Export Prediction Inferences to common formats """

    # ?format=(geojson/geojsonseq/csv)  [default: geojson]
    # ?inferences=all/<custom>          [default: all]
    # ?threshold=0->1                   [default 0]
    def get(self, model_id, prediction_id):
        req_format = request.args.get('format', 'geojson')
        req_inferences = request.args.get('inferences', 'all')
        req_threshold = request.args.get('threshold', '0')

        req_threshold = float(req_threshold)

        stream = PredictionService.export(prediction_id)

        inferences = PredictionService.inferences(prediction_id)
        first = False

        if req_inferences != 'all':
            inferences = [ req_inferences ]

        def generate():
            nonlocal first

            if req_format == "geojson":
                yield '{ "type": "FeatureCollection", "features": ['
            elif req_format == "csv":
                output = io.StringIO()
                rowdata = ["ID", "QuadKey", "QuadKeyGeom"]
                rowdata.extend(inferences)
                csv.writer(output, quoting=csv.QUOTE_NONNUMERIC).writerow(rowdata)
                yield output.getvalue()

            for row in stream:

                if req_inferences != 'all' and row[3].get(req_inferences) is None:
                    continue

                if req_inferences != 'all' and row[3].get(req_inferences) <= req_threshold:
                    continue

                if req_format == "geojson" or req_format == "geojsonld":
                    feat = {
                        "id": row[0],
                        "quadkey": row[1],
                        "type": "Feature",
                        "properties": row[3],
                        "geometry": json.loads(row[2])
                    }

                    if req_format == "geojsonld":
                        yield json.dumps(feat) + '\n'
                    elif req_format == "geojson":
                        if first == False:
                            first = True
                            yield '\n' + json.dumps(feat)
                        else:
                            yield ',\n' + json.dumps(feat)
                elif req_format == "csv":
                    output = io.StringIO()
                    rowdata = [ row[0], row[1], row[2] ]
                    for inf in inferences:
                        rowdata.append(row[3].get(inf, 0.0))
                    csv.writer(output, quoting=csv.QUOTE_NONNUMERIC).writerow(rowdata)
                    yield output.getvalue()
                else:
                    raise "Unsupported export format"

            if req_format == "geojson":
                yield ']}'



        if req_format == "csv":
            mime = "text/csv"
        elif req_format == "geojson":
            mime = "application/geo+json"
        elif req_format == "geojsonld":
            mime = "application/geo+json-seq"

        return Response(
            generate(),
            mimetype = mime,
            status = 200,
            headers = {
                "Content-Disposition": 'attachment; filename="export."' + req_format
            }
        )

class PredictionInfAPI(Resource):
    """ Add GeoJSON to SQS Inference Queue """

    def delete(self, model_id, prediction_id):
        if CONFIG.EnvironmentConfig.ENVIRONMENT != "aws":
            return {
                "status": 501,
                "error": "stack must be in 'aws' mode to use this endpoint"
            }, 501

        try:
            queues = response = boto3.client('sqs').list_queues(
                QueueNamePrefix="{stack}-models-{model}-prediction-{pred}-".format(
                    stack = CONFIG.EnvironmentConfig.STACK,
                    model = model_id,
                    pred = prediction_id
                )
            )

            for queue in queues['QueueUrls']:
                boto3.client('sqs').purge_queue(
                    QueueUrl=queue
                )

            return {
                "status": 200,
                "message": "queue purged"
            }, 200
        except Exception as e:
            if str(e).find("does not exist") != -1:
                return {
                    "name": stack,
                    "status": "None"
                }, 200
            else:
                error_msg = f'Prediction Stack Info Error: {str(e)}'
                current_app.logger.error(error_msg)
                return {
                    "status": 500,
                    "error": "Failed to get stack info"
                }, 500

    def get(self, model_id, prediction_id):
        if CONFIG.EnvironmentConfig.ENVIRONMENT != "aws":
            return {
                "status": 501,
                "error": "stack must be in 'aws' mode to use this endpoint"
            }, 501

        try:
            queues = response = boto3.client('sqs').list_queues(
                QueueNamePrefix="{stack}-models-{model}-prediction-{pred}-".format(
                    stack = CONFIG.EnvironmentConfig.STACK,
                    model = model_id,
                    pred = prediction_id
                )
            )


            active = ""
            dead = ""
            for queue in queues['QueueUrls']:
                if "-dead-queue" in queue:
                    dead = queue
                elif "-queue" in queue:
                    active = queue

            active = boto3.client('sqs').get_queue_attributes(
                QueueUrl=active,
                AttributeNames = [
                    'ApproximateNumberOfMessages',
                    'ApproximateNumberOfMessagesNotVisible'
                ]
            )

            dead = boto3.client('sqs').get_queue_attributes(
                QueueUrl=dead,
                AttributeNames = [
                    'ApproximateNumberOfMessages'
                ]
            )

            return {
                "queued": int(active['Attributes']['ApproximateNumberOfMessages']),
                "inflight": int(active['Attributes']['ApproximateNumberOfMessagesNotVisible']),
                "dead": int(dead['Attributes']['ApproximateNumberOfMessages'])
            }, 200
        except Exception as e:
            if str(e).find("does not exist") != -1:
                return {
                    "name": stack,
                    "status": "None"
                }, 200
            else:
                error_msg = f'Prediction Stack Info Error: {str(e)}'
                current_app.logger.error(error_msg)
                return {
                    "status": 500,
                    "error": "Failed to get stack info"
                }, 500

    def post(self, model_id, prediction_id):
        if CONFIG.EnvironmentConfig.ENVIRONMENT != "aws":
            return {
                "status": 501,
                "error": "stack must be in 'aws' mode to use this endpoint"
            }, 501

        payload = request.data

        tiler = tileschemes.WebMercator()

        try:
            prediction = PredictionService.get_prediction_by_id(prediction_id)

            poly = shape(geojson.loads(payload))

            project = partial(
                pyproj.transform,
                pyproj.Proj(init='epsg:4326'),
                pyproj.Proj(init='epsg:3857')
            )

            poly = transform(project, poly)

            tiles = tilecover.cover_geometry(tiler, poly, prediction.tile_zoom)

            queue_name = "{stack}-models-{model}-prediction-{prediction}-queue".format(
                stack=CONFIG.EnvironmentConfig.STACK,
                model=model_id,
                prediction=prediction_id
            )

            queue = boto3.resource('sqs').get_queue_by_name(
                QueueName=queue_name
            )

            cache = []
            for tile in tiles:
                if len(cache) < 10:
                    cache.append({
                        "Id": str(tile.z) + "-" + str(tile.x) + "-" + str(tile.y),
                        "MessageBody": json.dumps({
                            "x": tile.x,
                            "y": tile.y,
                            "z": tile.z
                        })
                    })
                else:
                    queue.send_messages(
                        Entries=cache
                    )
                    cache = []

            return {}, 200
        except Exception as e:
            error_msg = f'Predction Tiler Error: {str(e)}'
            current_app.logger.error(error_msg)
            return {
                "status": 500,
                "error": error_msg
            }, 500

class PredictionStacksAPI(Resource):
    def get(self):
        """
        Return a list of all running substacks
        ---
        produces:
            - application/json
        responses:
            200:
                description: ID of the prediction
        """

        stacks = []

        def getList():
            token = False;

            stack_res = boto3.client('cloudformation').list_stacks(
                StackStatusFilter = [
                    'CREATE_IN_PROGRESS',
                    'CREATE_COMPLETE',
                    'ROLLBACK_IN_PROGRESS',
                    'ROLLBACK_FAILED',
                    'ROLLBACK_COMPLETE',
                    'DELETE_IN_PROGRESS',
                    'DELETE_FAILED',
                    'UPDATE_IN_PROGRESS',
                    'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS',
                    'UPDATE_COMPLETE',
                    'UPDATE_ROLLBACK_IN_PROGRESS',
                    'UPDATE_ROLLBACK_FAILED',
                    'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS',
                    'UPDATE_ROLLBACK_COMPLETE',
                    'REVIEW_IN_PROGRESS',
                    'IMPORT_IN_PROGRESS',
                    'IMPORT_COMPLETE',
                    'IMPORT_ROLLBACK_IN_PROGRESS',
                    'IMPORT_ROLLBACK_FAILED',
                    'IMPORT_ROLLBACK_COMPLETE'
                ]
            )

            stacks.extend(stack_res.get("StackSummaries"))

            while stack_res.get("NextToken") is not None:
                print(stack_res.get("NextToken"))
                stack_res = boto3.client('cloudformation').list_stacks(
                    NextToken = stack_res.get("NextToken")
                )

                stacks.extend(stack_res.get("StackSummaries"))


        if CONFIG.EnvironmentConfig.ENVIRONMENT != "aws":
            return {
                "status": 501,
                "error": "stack must be in 'aws' mode to use this endpoint"
            }, 501

        try:
            getList()

            res = {
                "models": [],
                "predictions": [],
                "stacks": []
            }

            for stack in stacks:
                name = stack.get("StackName")
                if name.startswith(CONFIG.EnvironmentConfig.STACK + "-models-") and name not in res["stacks"]:
                    res["stacks"].append(stack.get("StackName"))

                    split = name.split('-')
                    model = int(split[len(split) - 3])
                    prediction = int(split[len(split) - 1])

                    if model not in res["models"]:
                        res["models"].append(model)
                    if prediction not in res["predictions"]:
                        res["predictions"].append(prediction)

            return res, 200

        except Exception as e:
            error_msg = f'Prediction Stack List Error: {str(e)}'
            current_app.logger.error(error_msg)
            return {
                "status": 500,
                "error": "Failed to get stack list"
            }, 500


class PredictionStackAPI(Resource):
    """ Create, Manage & Destroy Prediction Stacks """

    def post(self, model_id, prediction_id):
        if CONFIG.EnvironmentConfig.ENVIRONMENT != "aws":
            return {
                "status": 501,
                "error": "stack must be in 'aws' mode to use this endpoint"
            }, 501

        payload = request.get_json()

        if payload.get("imagery") is None:
            return {
                "status": 400,
                "error": "imagery key required in body"
            }, 400

        if payload.get("inferences") is None:
            return {
                "status": 400,
                "error": "inferences key required in body"
            }, 400

        image = "models-{model}-prediction-{prediction}".format(
            model=model_id,
            prediction=prediction_id
        )

        stack = "{stack}-{image}".format(
            stack=CONFIG.EnvironmentConfig.STACK,
            image=image
        )

        template = ''
        with open('cloudformation/prediction.template.json', 'r') as file:
            template = file.read()

        try:
            boto3.client('cloudformation').create_stack(
                StackName=stack,
                TemplateBody=template,
                Tags = payload.get("tags", []),
                Parameters=[{
                    'ParameterKey': 'GitSha',
                    'ParameterValue': CONFIG.EnvironmentConfig.GitSha,
                },{
                    'ParameterKey': 'StackName',
                    'ParameterValue': CONFIG.EnvironmentConfig.STACK,
                },{
                    'ParameterKey': 'ImageTag',
                    'ParameterValue': image,
                },{
                    'ParameterKey': 'Inferences',
                    'ParameterValue': payload["inferences"],
                },{
                    'ParameterKey': 'PredictionId',
                    'ParameterValue': str(prediction_id)
                },{
                    'ParameterKey': 'TileEndpoint',
                    'ParameterValue': payload["imagery"],
                },{
                    'ParameterKey': 'MaxSize',
                    'ParameterValue': payload.get("maxSize", "1"),
                },{
                    'ParameterKey': 'MaxConcurrency',
                    'ParameterValue': payload.get("maxConcurrency", "50"),
                }],
                Capabilities=[
                    'CAPABILITY_NAMED_IAM'
                ],
                OnFailure='ROLLBACK',
            )

            return self.get(model_id, prediction_id)
        except Exception as e:
            error_msg = f'Prediction Stack Creation Error: {str(e)}'
            current_app.logger.error(error_msg)
            return {
                "status": 500,
                "error": "Failed to create stack info"
            }, 500

    def delete(self, model_id, prediction_id):
        if CONFIG.EnvironmentConfig.ENVIRONMENT != "aws":
            return {
                "status": 501,
                "error": "stack must be in 'aws' mode to use this endpoint"
            }, 501

        try:
            stack = "{stack}-models-{model}-prediction-{prediction}".format(
                stack=CONFIG.EnvironmentConfig.STACK,
                model=model_id,
                prediction=prediction_id
            )

            boto3.client('cloudformation').delete_stack(
                StackName=stack
            )

            return self.get(model_id, prediction_id)
        except Exception as e:
            if str(e).find("does not exist") != -1:
                return {
                    "name": stack,
                    "status": "None"
                }, 200
            else:
                error_msg = f'Prediction Stack Info Error: {str(e)}'
                current_app.logger.error(error_msg)
                return {
                    "status": 500,
                    "error": "Failed to get stack info"
                }, 500

    def get(self, model_id, prediction_id):
        """
        Return status of a prediction stack
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

        if CONFIG.EnvironmentConfig.ENVIRONMENT != "aws":
            return {
                "status": 501,
                "error": "stack must be in 'aws' mode to use this endpoint"
            }, 501

        try:
            stack = "{stack}-models-{model}-prediction-{prediction}".format(
                stack=CONFIG.EnvironmentConfig.STACK,
                model=model_id,
                prediction=prediction_id
            )

            res = boto3.client('cloudformation').describe_stacks(
                StackName=stack
            )

            stack = {
                "id": res.get("Stacks")[0].get("StackId"),
                "name": stack,
                "status": res.get("Stacks")[0].get("StackStatus")
            }

            return stack, 200
        except Exception as e:
            if str(e).find("does not exist") != -1:
                return {
                    "name": stack,
                    "status": "None"
                }, 200
            else:
                error_msg = f'Prediction Stack Info Error: {str(e)}'
                current_app.logger.error(error_msg)
                return {
                    "status": 500,
                    "error": "Failed to get stack info"
                }, 500

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

        if CONFIG.EnvironmentConfig.ENVIRONMENT != "aws":
            return {
                "status": 501,
                "error": "stack must be in 'aws' mode to use this endpoint"
            }, 501

        if CONFIG.EnvironmentConfig.ASSET_BUCKET is None:
            return {
                "status": 501,
                "error": "Not Configured"
            }, 501

        key = "models/{0}/prediction/{1}/model.zip".format(
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
                return {
                    "status": 400,
                    "error": "Model not found in request"
                }, 400

            model = request.files[files[0]]

            # Save the model to S3
            try:
                boto3.resource('s3').Bucket(CONFIG.EnvironmentConfig.ASSET_BUCKET).put_object(
                    Key=key,
                    Body=model.stream
                )
            except Exception as e:
                error_msg = f'S3 Upload Error: {str(e)}'
                current_app.logger.error(error_msg)
                return {
                    "status": 500,
                    "error": "Failed to upload model to S3"
                }, 500

            # Save the model link to ensure UI shows upload success
            try:
                PredictionService.patch(prediction_id, {
                    "modelLink": CONFIG.EnvironmentConfig.ASSET_BUCKET + '/' + key
                })
            except Exception as e:
                error_msg = f'SaveLink Error: {str(e)}'
                current_app.logger.error(error_msg)
                return {
                    "status": 500,
                    "error": "Failed to save model state to DB"
                }, 500

            try:
                batch = boto3.client(
                    service_name='batch',
                    region_name='us-east-1',
                    endpoint_url='https://batch.us-east-1.amazonaws.com'
                )

                # Submit to AWS Batch to convert to ECR image
                batch.submit_job(
                    jobName=CONFIG.EnvironmentConfig.STACK + 'ecr-build',
                    jobQueue=CONFIG.EnvironmentConfig.STACK + '-queue',
                    jobDefinition=CONFIG.EnvironmentConfig.STACK + '-job',
                    containerOverrides={
                        'environment': [{
                            'name': 'MODEL',
                            'value': CONFIG.EnvironmentConfig.ASSET_BUCKET + '/' + key
                        }]
                    }
                )
            except Exception as e:
                error_msg = f'Batch Error: {str(e)}'
                current_app.logger.error(error_msg)
                return {
                    "status": 500,
                    "error": "Failed to start ECR build"
                }, 500

            return { "status": "model uploaded" }, 200
        else:
            return {
                "status": 400,
                "error": "model exists"
            }, 400

class PredictionValidity(Resource):
    def post(self, model_id, prediction_id):
        try:
            payload = request.get_json()

            inferences = PredictionService.inferences(prediction_id)

            final = {}
            for inf in inferences:
                p = payload.get(inf)

                if p is None or type(p) is not bool:
                    continue

                final[inf] = payload.get(inf)

            tile = PredictionTileService.get(28455)
            if tile is None:
                return {
                    "status": 404,
                    "error": "model not found"
                }, 404

            tile = tile.validity
            if tile is None:
                current = {}

            print(current, final)

        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return {
                "status": 500,
                "error": error_msg
            }, 500

class PredictionSingleAPI(Resource):
    def get(self, model_id, prediction_id):
        try:
            prediction = PredictionService.get_prediction_by_id(prediction_id)
            version = MLModelVersion.get(prediction.version_id)

            pred = {
                "predictionsId": prediction.id,
                "modelId": prediction.model_id,
                "versionId": prediction.version_id,
                "versionString": f'{version.version_major}.{version.version_minor}.{version.version_patch}',
                "dockerUrl": prediction.docker_url,
                "tileZoom": prediction.tile_zoom,
                "logLink": prediction.log_link,
                "modelLink": prediction.model_link,
                "dockerLink": prediction.docker_link,
                "saveLink": prediction.save_link
            }

            return pred, 200
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return {
                "status": 500,
                "error": error_msg
            }, 500


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
                return {
                    "status": 500,
                    "error": error_msg
                }, 500
        except NotFound:
            return {
                "status": 404,
                "error": "model not found"
            }, 404
        except DataError as e:
            current_app.logger.error(f'Error validating request: {str(e)}')
            return {
                "status": 400,
                "error": str(e)
            }, 400
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return {
                "status": 500,
                "error": error_msg
            }, 500

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
                return {
                    "status": 400,
                    "error": 'A bbox is required'
                }, 400

            # check if this model exists
            ml_model_dto = MLModelService.get_ml_model_by_id(model_id)

            boundingBox = bbox_str_to_list(bbox)
            predictions = PredictionService.get(ml_model_dto.model_id, boundingBox)
            return predictions, 200
        except PredictionsNotFound:
            return {
                "status": 404,
                "error": "Predictions not found"
            }, 404
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return {
                "status": 500,
                "error": error_msg
            }, 500

    def patch(self, model_id, prediction_id):
        """
        Allow updating of links in model
        ---
        produces:
            - application/json
        parameters:
            - in: path
              name: model_id
              description: ID of the Model
              required: true
              type: integer
            - in: path
              name: prediction_id
              description: ID of the Prediction
              required: true
              type: integer
        responses:
            200:
                description: Prediction updated successfully
            404:
                description: Prediction not found to update
            500:
                description: Internal Server Error
        """
        try:
            updated_prediction = request.get_json()

            if updated_prediction is None:
                return {
                    "status": 400,
                    "error": "prediction must be json object"
                }, 400

            prediction_id = PredictionService.patch(prediction_id, updated_prediction)

            return {
                "model_id": model_id,
                "prediction_id": prediction_id
            }, 200
        except NotFound:
            return {
                "status": 404,
                "error": "prediction not found"
            }, 404
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return {
                "status": 500,
                "error": error_msg
            }, 500

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
            return {
                "status": 404,
                "error": "Predictions not found"
            }, 404
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return {
                "status": 500,
                "error": error_msg
            }, 500

class PredictionTileMVT(Resource):
    """
    Methods to retrieve vector tiles
    """

    def get(self, model_id, prediction_id, z, x, y):
        """
        Mapbox Vector Tile Response
        ---
        produces:
            - application/x-protobuf
        parameters:
            - in: path
              name: model_id
              description: ID of the Model
              required: true
              type: integer
            - in: path
              name: prediction_id
              description: ID of the Prediction
              required: true
              type: integer
            - in: path
              name: z
              description: zoom of the tile to fetch
              required: true
              type: integer
            - in: path
              name: y
              description: y coord of the tile to fetch
              required: true
              type: integer
            - in: path
              name: x
              description: x coord of the tile to fetch
              required: true
              type: integer
        responses:
            200:
                description: ID of the prediction
            400:
                description: Invalid Request
            500:
                description: Internal Server Error
        """

        try:
            tile = PredictionTileService.mvt(model_id, prediction_id, z, x, y)

            response = make_response(tile)
            response.headers['content-type'] = 'application/x-protobuf'

            return response
        except PredictionsNotFound:
            return {
                "status": 404,
                "error": "Prediction tile not found"
            }, 404
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return {
                "status": 500,
                "error": error_msg
            }, 500

class PredictionTileAPI(Resource):
    """
    Methods to manage tile predictions
    """

    def get(self, model_id, prediction_id):
        """
        TileJSON response for the predictions
        ---
        produces:
            - application/json
        parameters:
            - in: path
              name: model_id
              description: ID of the Model
              required: true
              type: integer
            - in: path
              name: prediction_id
              description: ID of the Prediction
              required: true
              type: integer
        responses:
            200:
                description: ID of the prediction
            400:
                description: Invalid Request
            500:
                description: Internal Server Error
        """

        try:
            return PredictionTileService.tilejson(model_id, prediction_id)
        except PredictionsNotFound:
            return {
                "status": 404,
                "error": "Prediction TileJSON not found"
            }, 404
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return {
                "status": 500,
                "error": error_msg
            }, 500

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
            data = request.get_json()
            if (len(data['predictions']) == 0):
                return {
                    "status": 400,
                    "error": "Error validating request"
                }, 400

            PredictionTileService.create(data)

            return {"prediction_id": prediction_id}, 200
        except PredictionsNotFound:
            return {
                "status": 404,
                "error": "Prediction not found"
            }, 404
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return {
                "status": 500,
                "error": error_msg
            }, 500


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
                return {
                    "status": 400,
                    "error": 'A bbox is required'
                }, 400

            if (zoom is None or zoom == ''):
                return {
                    "status": 400,
                    "error": 'Zoom level is required for aggregation'
                }, 400

            # check if this model exists
            ml_model_dto = MLModelService.get_ml_model_by_id(model_id)
            tiles = PredictionTileService.get_aggregated_tiles(
                    ml_model_dto.model_id, bbox, zoom)
            return tiles, 200

        except NotFound:
            return {
                "status": 404,
                "error": "Model not found"
            }, 404
        except PredictionsNotFound:
            return {
                "status": 404,
                "error": "No predictions for this bbox"
            }, 404
        except ValueError as e:
            return {
                "status": 400,
                "error": str(e)
            }, 400
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return {
                "status": 500,
                "error": error_msg
            }, 500


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
            return {
                "status": 400,
                "error": "Invalid GeoJSON"
            }, 400
        except NotFound:
            return {
                "status": 404,
                "error": "Model not found"
            }, 404
        except PredictionsNotFound:
            return {
                "status": 404,
                "error": "No predictions for this bbox"
            }, 404
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return {
                "status": 500,
                "error": error_msg
            }, 500
