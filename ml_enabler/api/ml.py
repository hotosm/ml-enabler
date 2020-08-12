import ml_enabler.config as CONFIG
import io, os, pyproj, json, csv, geojson, boto3, mercantile
from tiletanic import tilecover, tileschemes
from shapely.geometry import shape
from shapely.ops import transform
from functools import partial
from flask import make_response
from flask_restful import Resource, request, current_app
from flask import Response
from ml_enabler.models.dtos.ml_model_dto import MLModelDTO, PredictionDTO
from schematics.exceptions import DataError
from ml_enabler.services.ml_model_service import MLModelService
from ml_enabler.services.prediction_service import PredictionService, PredictionTileService
from ml_enabler.services.imagery_service import ImageryService
from ml_enabler.services.task_service import TaskService
from ml_enabler.utils import err
from ml_enabler.models.utils import NotFound, VersionNotFound, \
    PredictionsNotFound, ImageryNotFound
from ml_enabler.utils import version_to_array, geojson_bounds, bbox_str_to_list, validate_geojson, InvalidGeojson, NoValid
from sqlalchemy.exc import IntegrityError
from flask_login import login_required
import numpy as np

import logging
from flask import Flask
app = Flask(__name__)
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)




class MetaAPI(Resource):

    """
    Return metadata about the API
    """
    def get(self):
        # -- NOT AUTHENTICATED --
        # Do not put sensitive data in this response
        return {
            'version': 1,
            'environment': CONFIG.EnvironmentConfig.ENVIRONMENT,
            'security': 'authenticated'
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

    @login_required
    def get(self):
        return {
            "token": CONFIG.EnvironmentConfig.MAPBOX_TOKEN
        }, 200

class MLModelAPI(Resource):

    @login_required
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

    @login_required
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
            return err(404, "model not found"), 404
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return err(500, error_msg), 500

    @login_required
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
            return err(404, "model not found"), 404
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return err(500, error_msg), 500

    @login_required
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
            return err(404, "model not found"), 404
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return err(500, error_msg), 500

class GetAllModels(Resource):
    """ Methods to fetch many ML models """

    @login_required
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
        model_filter = request.args.get('filter', '')
        model_archived = request.args.get('archived', 'false')

        if model_archived == 'false':
            model_archived = False
        elif model_archived == 'true':
            model_archived = True
        else:
            return err(400, "archived param must be 'true' or 'false'"), 400

        try:
            ml_models = MLModelService.get_all(model_filter, model_archived)
            return ml_models, 200
        except NotFound:
            return err(404, "no models found"), 404
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return err(500, error_msg), 500

class ImageryAPI(Resource):
    """ Upload imagery sources for a given model """

    @login_required
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

    @login_required
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


    @login_required
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
            return err(500, "Failed to save imagery source to DB"), 500

    @login_required
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
            return err(404, "Imagery not found"), 404
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return err(500, error_msg), 500

class PredictionExport(Resource):
    """ Export Prediction Inferences to common formats """

    # ?format=(geojson/geojsonseq/csv)  [default: geojson]
    # ?inferences=all/<custom>          [default: all]
    # ?threshold=0->1                   [default 0]

    @login_required
    def get(self, model_id, prediction_id):
        req_format = request.args.get('format', 'geojson')
        req_inferences = request.args.get('inferences', 'all')
        req_threshold = request.args.get('threshold', '0')
        req_threshold = float(req_threshold)

        stream = PredictionService.export(prediction_id)

        inferences = PredictionService.inferences(prediction_id)

        pred = PredictionService.get_prediction_by_id(prediction_id)

        first = False

        if req_inferences != 'all':
            inferences = [ req_inferences ]

        def generate_npz():
            nonlocal req_threshold
            labels_dict ={}

            for row in stream:
                if req_inferences != 'all' and row[3].get(req_inferences) is None:
                    continue

                if req_inferences != 'all' and row[3].get(req_inferences) <= req_threshold:
                    continue
                if row[4]:
                    i_lst = pred.inf_list.split(",")

                    #convert raw predictions into 0 or 1 based on threshold
                    raw_pred = []
                    for num, inference in enumerate(i_lst):
                        raw_pred.append(row[3][inference])
                    if  req_inferences == 'all':

                        req_threshold = request.args.get('threshold', '0.5')
                        req_threshold = float(req_threshold)
                    l = [1 if score >= req_threshold else 0 for score in raw_pred]

                    #convert quadkey to x-y-z
                    t = '-'.join([str(i) for i in mercantile.quadkey_to_tile(row[1])])

                    # special case for binary
                    if (pred.inf_binary) and (len(i_lst) != 2):
                        return err(400, "binary models must have two catagories"), 400
                    if (len(i_lst) == 2) and (pred.inf_binary):
                        if list(row[4].values())[0]: #validated and true, keep original
                            labels_dict.update({t:l})
                        else:
                            if l == [1, 0]:
                                l = [0, 1]
                            else:
                                l = [1, 0]
                            labels_dict.update({t:l})
                    else:
                        # for multi-label
                        for key in list(row[4].keys()):
                            i = i_lst.index(key)
                            if not row[4][key]:
                                if l[i] == 0:
                                    l[i] = 1
                                else:
                                    l[i] = 0
                            labels_dict.update({t:l})
            if not labels_dict:
                raise NoValid

            bytestream = io.BytesIO()
            np.savez(bytestream, **labels_dict)
            return bytestream.getvalue()

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
                    properties_dict = {}
                    if row[4]:
                        properties_dict = row[3]
                        valid_dict = {}
                        valid_dict.update({'validity': row[4]})
                        properties_dict.update(valid_dict)
                    else:
                        properties_dict = row[3]
                    feat = {
                        "id": row[0],
                        "quadkey": row[1],
                        "type": "Feature",
                        "properties": properties_dict,
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
                    rowdata = [ row[0], row[1], row[2]]
                    for inf in inferences:
                        rowdata.append(row[3].get(inf, 0.0))
                    csv.writer(output, quoting=csv.QUOTE_NONNUMERIC).writerow(rowdata)
                    yield output.getvalue()
                else:
                    return err(501, "not a valid export type, valid export types are: geojson, csv, and npz"), 501

            if req_format == "geojson":
                yield ']}'

        if req_format == "csv":
            mime = "text/csv"
        elif req_format == "geojson":
            mime = "application/geo+json"
        elif req_format == "geojsonld":
            mime = "application/geo+json-seq"
        elif req_format == "npz":
            mime = "application/npz"
        if req_format == "npz":
            try:
                npz = generate_npz()
                return Response(
                response = generate_npz(),
                mimetype = mime,
                status = 200,
                headers = {
                    "Content-Disposition": 'attachment; filename="export.' + req_format + '"'
                }
            )
            except NoValid:
                return err(400, "Can only return npz if predictions are validated. Currently there are no valid predictions"), 400
        else:
            return Response(
                generate(),
                mimetype = mime,
                status = 200,
                headers = {
                    "Content-Disposition": 'attachment; filename="export.' + req_format + '"'
                }
            )

class PredictionInfAPI(Resource):
    """ Add GeoJSON to SQS Inference Queue """

    @login_required
    def delete(self, model_id, prediction_id):
        if CONFIG.EnvironmentConfig.ENVIRONMENT != "aws":
            return err(501, "stack must be in 'aws' mode to use this endpoint"), 501

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
                return err(500, "Failed to get stack info"), 500

    @login_required
    def get(self, model_id, prediction_id):
        if CONFIG.EnvironmentConfig.ENVIRONMENT != "aws":
            return err(501, "stack must be in 'aws' mode to use this endpoint"), 501

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
                return err(500, "Failed to get stack info"), 500

    @login_required
    def post(self, model_id, prediction_id):
        if CONFIG.EnvironmentConfig.ENVIRONMENT != "aws":
            return err(501, "stack must be in 'aws' mode to use this endpoint"), 501

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
            return err(500, error_msg), 500

class PredictionRetrain(Resource):
    @login_required
    def post(self, model_id, prediction_id):
        """
        Retrain a model with validated predictions
        ---
        produces:
            - application/json
        """

        if CONFIG.EnvironmentConfig.ENVIRONMENT != "aws":
            return err(501, "stack must be in 'aws' mode to use this endpoint"), 501

        if CONFIG.EnvironmentConfig.ASSET_BUCKET is None:
            return err(501, "Not Configured"), 501

        payload = request.get_json()

        if payload.get("imagery") is None:
            return err(400, "imagery key required in body"), 400

        try:
            batch = boto3.client(
                service_name='batch',
                region_name='us-east-1',
                endpoint_url='https://batch.us-east-1.amazonaws.com'
            )

            # Submit to AWS Batch to convert to ECR image
            job = batch.submit_job(
                jobName=CONFIG.EnvironmentConfig.STACK + '-retrain',
                jobQueue=CONFIG.EnvironmentConfig.STACK + '-gpu-queue',
                jobDefinition=CONFIG.EnvironmentConfig.STACK + '-gpu-job',
                containerOverrides={
                    'environment': [
                        { 'name': 'MODEL_ID', 'value': str(model_id) },
                        { 'name': 'PREDICTION_ID', 'value': str(prediction_id) },
                        { 'name': 'TILE_ENDPOINT', 'value': payload.get("imagery") },
                    ]
                }
            )

            TaskService.create({
                'pred_id': prediction_id,
                'type': 'retrain',
                'batch_id': job.get('jobId')
            })
        except Exception as e:
            error_msg = f'Batch GPU Error: {str(e)}'
            current_app.logger.error(error_msg)
            return err(500, "Failed to start GPU Retrain"), 500

class PredictionStacksAPI(Resource):
    @login_required
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
            return err(501, "stack must be in 'aws' mode to use this endpoint"), 501

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
            return err(500, "Failed to get stack list"), 500


class PredictionStackAPI(Resource):
    """ Create, Manage & Destroy Prediction Stacks """

    @login_required
    def post(self, model_id, prediction_id):
        if CONFIG.EnvironmentConfig.ENVIRONMENT != "aws":
            return err(501, "stack must be in 'aws' mode to use this endpoint"), 501

        payload = request.get_json()

        if payload.get("imagery") is None:
            return err(400, "imagery key required in body"), 400

        pred = PredictionService.get_prediction_by_id(prediction_id)
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
                    'ParameterKey': 'MachineAuth',
                    'ParameterValue': CONFIG.EnvironmentConfig.MACHINE_AUTH
                },{
                    'ParameterKey': 'StackName',
                    'ParameterValue': CONFIG.EnvironmentConfig.STACK,
                },{
                    'ParameterKey': 'ImageTag',
                    'ParameterValue': image,
                },{
                    'ParameterKey': 'Inferences',
                    'ParameterValue': pred.inf_list,
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
                },{
                    'ParameterKey': 'InfSupertile',
                    'ParameterValue': str(pred.inf_supertile),

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
            return err(500, "Failed to create stack info"), 500

    @login_required
    def delete(self, model_id, prediction_id):
        if CONFIG.EnvironmentConfig.ENVIRONMENT != "aws":
            return err(501, "stack must be in 'aws' mode to use this endpoint"), 501

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
                return err(500, "Failed to get stack info"), 500

    @login_required
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
            return err(501, "stack must be in 'aws' mode to use this endpoint"), 501

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
                return err(500, "Failed to get stack info"), 500

class PredictionUploadAPI(Resource):
    """ Upload raw ML Models to the platform """

    @login_required
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
            return err(501, "stack must be in 'aws' mode to use this endpoint"), 501

        if CONFIG.EnvironmentConfig.ASSET_BUCKET is None:
            return err(501, "Not Configured"), 501

        modeltype = request.args.get('type', 'model')
        if modeltype not in ["model", "tfrecord", "checkpoint"]:
            return err(400, "Unsupported type param"), 400

        key = "models/{0}/prediction/{1}/{2}.zip".format(
            model_id,
            prediction_id,
            modeltype
        )

        try:
            boto3.client('s3').head_object(
                Bucket=CONFIG.EnvironmentConfig.ASSET_BUCKET,
                Key=key
            )
        except:
            files = list(request.files.keys())
            if len(files) == 0:
                return err(400, "Model not found in request"), 400

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
                return err(500, "Failed to upload model to S3"), 500

            if modeltype == "checkpoint":
                try:
                    PredictionService.patch(prediction_id, {
                        "checkpointLink": CONFIG.EnvironmentConfig.ASSET_BUCKET + '/' + key
                    })
                except Exception as e:
                    error_msg = f'SaveLink Error: {str(e)}'
                    current_app.logger.error(error_msg)
                    return err(500, "Failed to save checkpoint state to DB"), 500

            if modeltype == "tfrecord":
                try:
                    PredictionService.patch(prediction_id, {
                        "tfrecordLink": CONFIG.EnvironmentConfig.ASSET_BUCKET + '/' + key
                    })
                except Exception as e:
                    error_msg = f'SaveLink Error: {str(e)}'
                    current_app.logger.error(error_msg)
                    return err(500, "Failed to save checkpoint state to DB"), 500

            if modeltype == "model":
                # Save the model link to ensure UI shows upload success
                try:
                    PredictionService.patch(prediction_id, {
                        "modelLink": CONFIG.EnvironmentConfig.ASSET_BUCKET + '/' + key
                    })
                except Exception as e:
                    error_msg = f'SaveLink Error: {str(e)}'
                    current_app.logger.error(error_msg)
                    return err(500, "Failed to save model state to DB"), 500

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
                    return err(500, "Failed to start ECR build"), 500

            return { "status": "model uploaded" }, 200
        else:
            return err(400, "model exists"), 400

class PredictionValidity(Resource):
    @login_required
    def post(self, model_id, prediction_id):
        try:
            payload = request.get_json()

            inferences = PredictionService.inferences(prediction_id)

            if payload.get("id") is None or payload.get("validity") is None:
                return err(400, "id and validity keys must be present"), 400

            tile = PredictionTileService.get(payload["id"])
            if tile is None:
                return err(404, "prediction tile not found"), 404

            current = tile.validity
            if current is None:
                current = {}

            for inf in inferences:
                p = payload["validity"].get(inf)

                if p is None or type(p) is not bool:
                    continue

                current[inf] = p

            PredictionTileService.validity(payload["id"], current)

            return current, 200
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return (500, error_msg), 500

class PredictionSingleAPI(Resource):
    @login_required
    def get(self, model_id, prediction_id):
        try:
            prediction = PredictionService.get_prediction_by_id(prediction_id)

            pred = {
                "predictionsId": prediction.id,
                "modelId": prediction.model_id,
                "version": prediction.version,
                "dockerUrl": prediction.docker_url,
                "tileZoom": prediction.tile_zoom,
                "logLink": prediction.log_link,
                "modelLink": prediction.model_link,
                "dockerLink": prediction.docker_link,
                "saveLink": prediction.save_link,
                "infSupertile": prediction.inf_supertile,
                "tfrecordLink": prediction.tfrecord_link,
                "checkpointLink": prediction.checkpoint_link,
                "infList": prediction.inf_list,
                "infBinary": prediction.inf_binary,
                "infType": prediction.inf_type
            }

            return pred, 200
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return err(500, error_msg), 500


class PredictionAPI(Resource):
    """ Methods to manage ML predictions """

    @login_required
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

            # check if this model exists
            ml_model_dto = MLModelService.get_ml_model_by_id(model_id)

            # check if the version is registered
            prediction_id = PredictionService.create(model_id, payload)

            return {"prediction_id": prediction_id}, 200
        except NotFound:
            return err(404, "model not found"), 404
        except DataError as e:
            current_app.logger.error(f'Error validating request: {str(e)}')
            return err(400, str(4)), 400
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return err(500, error_msg), 500

    @login_required
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
                return err(400, "prediction must be json object"), 400

            prediction_id = PredictionService.patch(prediction_id, updated_prediction)

            return {
                "model_id": model_id,
                "prediction_id": prediction_id
            }, 200
        except NotFound:
            return err(404, "prediction not found"), 404
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return err(500, error_msg), 500

class GetAllPredictions(Resource):
    @login_required
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
            return err(404, "Predictions not found"), 404
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return err(500, error_msg), 500

class PredictionTileMVT(Resource):
    """
    Methods to retrieve vector tiles
    """

    @login_required
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
            return err(404, "Prediction tile not found"), 404
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return err(500, error_msg), 500

class PredictionTileAPI(Resource):
    """
    Methods to manage tile predictions
    """

    @login_required
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
            return err(404, "Prediction TileJSON not found"), 404
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return err(500, error_msg), 500

    @login_required
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
                return err(400, "Error validating request"), 400

            PredictionTileService.create(data)

            return {"prediction_id": prediction_id}, 200
        except PredictionsNotFound:
            return err(404, "Prediction not found"), 404
        except Exception as e:
            error_msg = f'Unhandled error: {str(e)}'
            current_app.logger.error(error_msg)
            return err(500, error_msg), 500

