"""Example AWS Lambda function for chip-n-scale"""

import os
from typing import Dict, Any

from download_and_predict.base import DownloadAndPredict
from download_and_predict.custom_types import SQSEvent

def handler(event: SQSEvent, context: Dict[str, Any]) -> None:
    # read all our environment variables to throw errors early
    imagery = os.getenv('TILE_ENDPOINT')
    inferences = os.getenv('INFERENCES')
    prediction_endpoint = os.getenv('PREDICTION_ENDPOINT')
    mlenabler_endpoint = os.getenv('MLENABLER_ENDPOINT')

    assert(imagery)
    assert(inferences)
    assert(prediction_endpoint)
    assert(mlenabler_endpoint)

    # instantiate our DownloadAndPredict class
    dap = DownloadAndPredict(
        imagery=imagery,
        prediction_endpoint=prediction_endpoint
    )

    # get tiles from our SQS event
    tiles = dap.get_tiles(event)

    # construct a payload for our prediction endpoint
    tile_indices, payload = dap.get_prediction_payload(tiles)

    # send prediction request
    content = dap.post_prediction(payload)

    print(content);
