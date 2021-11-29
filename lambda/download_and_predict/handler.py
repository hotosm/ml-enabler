"""Example AWS Lambda function for chip-n-scale"""

import os
from typing import Dict, Any
from download_and_predict.base import MLEnabler, DownloadAndPredict, ModelType, SuperTileDownloader
from download_and_predict.custom_types import SQSEvent

def handler(event: SQSEvent, context: Dict[str, Any]) -> bool:
    # read all our environment variables to throw errors early
    auth = os.getenv('MACHINE_AUTH')
    imagery_id = os.getenv('IMAGERY_ID')
    model_id = os.getenv('MODEL_ID')
    prediction_id = os.getenv('PREDICTION_ID')
    prediction_endpoint = os.getenv('PREDICTION_ENDPOINT')
    mlenabler_endpoint = os.getenv('MLENABLER_ENDPOINT')
    super_tile = os.getenv('INF_SUPERTILE')

    assert(auth)
    assert(imagery_id)
    assert(model_id)
    assert(prediction_id)
    assert(prediction_endpoint)
    assert(mlenabler_endpoint)

    ml = MLEnabler(mlenabler_endpoint)
    imagery = ml.get_imagery(
        model_id=model_id,
        imagery_id=imagery_id
    )

    # instantiate our DownloadAndPredict class
    dap = DownloadAndPredict(
        imagery=imagery.get('url'),
        mlenabler_endpoint=mlenabler_endpoint,
        prediction_endpoint=prediction_endpoint
    )

    # get tiles from our SQS event
    tiles = dap.get_tiles(event)

    # Get meta about model to determine model type (Classification vs Object Detection)
    model_type = dap.get_meta()

    # construct a payload for our prediction endpoint

    if super_tile == 'True':
        dap = SuperTileDownloader(imagery=imagery.get('url'), mlenabler_endpoint=mlenabler_endpoint, prediction_endpoint=prediction_endpoint)
        tile_indices, payload = dap.get_prediction_payload(tiles, model_type)
    else:
        tile_indices, payload = dap.get_prediction_payload(tiles, model_type)

    if model_type == ModelType.OBJECT_DETECT:
        print("TYPE: Object Detection")

        # send prediction request
        preds = dap.od_post_prediction(payload, tiles, prediction_id)

        if len(preds["predictions"]) == 0:
            print('RESULT: No Predictions')
        else:
            print('RESULT: ' + str(len(preds["predictions"])) + ' Predictions')

            # Save the prediction to ML-Enabler
            dap.save_prediction(prediction_id, preds, auth)
    elif model_type == ModelType.CLASSIFICATION:
        print("TYPE: Classification")

        inferences = os.getenv('INFERENCES')
        assert(inferences)
        inferences = inferences.split(',')

        # send prediction request
        preds = dap.cl_post_prediction(payload, tiles, prediction_id, inferences)

        # Save the prediction to ML-Enabler
        dap.save_prediction(prediction_id, preds, auth)
    else:
        print("Unknown Model")

    return True

