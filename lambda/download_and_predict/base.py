"""
Lambda for downloading images, packaging them for prediction, sending them
to a remote ML serving image, and saving them
@author:Development Seed
"""

import json
from functools import reduce
from io import BytesIO
from base64 import b64encode
from urllib.parse import urlparse
from typing import Dict, List, NamedTuple, Callable, Optional, Tuple, Any, Iterator

import mercantile
from mercantile import Tile
import requests

from download_and_predict.custom_types import SQSEvent

class DownloadAndPredict(object):
    """
    base object DownloadAndPredict implementing all necessary methods to
    make machine learning predictions
    """

    def __init__(self, imagery: str, inferences: List[str], mlenabler_endpoint: str, prediction_endpoint: str):
        super(DownloadAndPredict, self).__init__()

        self.imagery = imagery
        self.inferences = inferences
        self.mlenabler_endpoint = mlenabler_endpoint
        self.prediction_endpoint = prediction_endpoint

    @staticmethod
    def get_tiles(event: SQSEvent) -> List[Tile]:
        """
        Return the body of our incoming SQS messages as an array of mercantile Tiles
        Expects events of the following format:

        { 'Records': [ { "body": '{ "x": 4, "y": 5, "z":3 }' }] }

        """
        return [
          Tile(*json.loads(record['body']).values())
          for record
          in event['Records']
        ]


    @staticmethod
    def b64encode_image(image_binary:bytes) -> str:
        return b64encode(image_binary).decode('utf-8')


    def get_images(self, tiles: List[Tile]) -> Iterator[Tuple[Tile, bytes]]:
        for tile in tiles:
            url = self.imagery.format(x=tile.x, y=tile.y, z=tile.z)
            print("IMAGE: " + url)
            r = requests.get(url)
            yield (tile, r.content)


    def get_prediction_payload(self, tiles:List[Tile]) -> Tuple[List[Tile], str]:
        """
        tiles: list mercantile Tiles
        imagery: str an imagery API endpoint with three variables {z}/{x}/{y} to replace

        Return:
        - an array of b64 encoded images to send to our prediction endpoint
        - a corresponding array of tile indices

        These arrays are returned together because they are parallel operations: we
        need to match up the tile indicies with their corresponding images
        """
        tiles_and_images = self.get_images(tiles)
        tile_indices, images = zip(*tiles_and_images)

        instances = [dict(image_bytes=dict(b64=self.b64encode_image(img))) for img in images]
        payload = json.dumps({
            "instances": instances
        })

        return (list(tile_indices), payload)

    def post_prediction(self, payload: str, tiles: List[Tile], prediction_id: str) -> List[Dict[str, Any]]:
        r = requests.post(self.prediction_endpoint, data=payload)
        r.raise_for_status()

        preds = r.json()["predictions"]
        pred_list = [];

        for i in range(len(tiles)):
            pred_dict = {}

            for j in range(len(preds[i])):
                pred_dict[self.inferences[j]] = preds[i][j]

            pred_list.append({
                "quadkey": mercantile.quadkey(tiles[i].x, tiles[i].y, tiles[i].z),
                "predictions": pred_dict,
                "prediction_id": prediction_id
            })

        return {
            "predictionId": prediction_id,
            "predictions": pred_list
        }

    def save_prediction(self, prediction_id: str, payload):
        url = self.mlenabler_endpoint + "/v1/model/prediction/" + prediction_id + "/tiles"
        r = requests.post(url, data=payload)
        r.raise_for_status()

        print(r.text)

        return true
