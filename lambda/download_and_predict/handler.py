"""Example AWS Lambda function for chip-n-scale"""

import os
from typing import Dict, Any

from download_and_predict.base import DownloadAndPredict
from download_and_predict.custom_types import SQSEvent

def handler(event: SQSEvent, context: Dict[str, Any]) -> None:
    # read all our environment variables to throw errors early
    imagery = os.getenv('TILE_ENDPOINT')
    inferences = os.getenv('INFERENCES')
    prediction_id = os.getenv('PREDICTION_ID')
    prediction_endpoint = os.getenv('PREDICTION_ENDPOINT')
    mlenabler_endpoint = os.getenv('MLENABLER_ENDPOINT')

    assert(imagery)
    assert(inferences)
    assert(prediction_id)
    assert(prediction_endpoint)
    assert(mlenabler_endpoint)

    inferences = inferences.split(',')

    # instantiate our DownloadAndPredict class
    dap = DownloadAndPredict(
        imagery=imagery,
        inferences=inferences,
        mlenabler_endpoint=mlenabler_endpoint,
        prediction_endpoint=prediction_endpoint
    )

    # Get meta about model to determine model type (Classification vs Object Detection)
    dap.get_meta()

    # get tiles from our SQS event
    tiles = dap.get_tiles(event)

    # construct a payload for our prediction endpoint
    tile_indices, payload = dap.get_prediction_payload(tiles)

    # send prediction request
    preds = dap.post_prediction(payload, tiles, prediction_id)

    print(preds);

    # Save the prediction to ML-Enabler
    dap.save_prediction(prediction_id, preds)

