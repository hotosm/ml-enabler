"""Example AWS Lambda function for chip-n-scale"""

import os
from typing import Dict, Any

from download_and_predict.base import DownloadAndPredict, ModelType
from download_and_predict.custom_types import SQSEvent

def handler(event: SQSEvent, context: Dict[str, Any]) -> Bool:
    # read all our environment variables to throw errors early
    imagery = os.getenv('TILE_ENDPOINT')
    prediction_id = os.getenv('PREDICTION_ID')
    prediction_endpoint = os.getenv('PREDICTION_ENDPOINT')
    mlenabler_endpoint = os.getenv('MLENABLER_ENDPOINT')

    assert(imagery)
    assert(prediction_id)
    assert(prediction_endpoint)
    assert(mlenabler_endpoint)

    # instantiate our DownloadAndPredict class
    dap = DownloadAndPredict(
        imagery=imagery,
        mlenabler_endpoint=mlenabler_endpoint,
        prediction_endpoint=prediction_endpoint
    )

    # get tiles from our SQS event
    tiles = dap.get_tiles(event)

    # Get meta about model to determine model type (Classification vs Object Detection)
    model_type = dap.get_meta()

    # construct a payload for our prediction endpoint
    tile_indices, payload = dap.get_prediction_payload(tiles, model_type)

    if model_type == ModelType.OBJECT_DETECT:
        print("TYPE: Object Detection")

        # send prediction request
        preds = dap.od_post_prediction(payload, tiles, prediction_id)

        print(preds);

        if len(preds["predictions"]) == 0:
            print('RESULT: No Predictions')
        else:
            print('RESULT: ' + str(len(preds["predictions"])) + ' Predictions')

            # Save the prediction to ML-Enabler
            dap.save_prediction(prediction_id, preds)
    elif model_type == ModelType.CLASSIFICATION:
        print("TYPE: Classification")

        inferences = os.getenv('INFERENCES')
        assert(inferences)
        inferences = inferences.split(',')

        # send prediction request
        preds = dap.cl_post_prediction(payload, tiles, prediction_id, inferences)

        print(preds);

        # Save the prediction to ML-Enabler
        dap.save_prediction(prediction_id, preds)
    else:
        print("Unknown Model")

    return True
