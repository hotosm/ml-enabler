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

from mercantile import Tile
import requests
import pg8000

from download_and_predict.custom_types import SQSEvent

class DownloadAndPredict(object):
    """
    base object DownloadAndPredict implementing all necessary methods to
    make machine learning predictions
    """

    def __init__(self, imagery: str, prediction_endpoint: str):
        super(DownloadAndPredict, self).__init__()
        self.imagery = imagery
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
        payload = json.dumps(dict(instances=instances))

        return (list(tile_indices), payload)

    def post_prediction(self, payload:str) -> Dict[str, Any]:
        r = requests.post(self.prediction_endpoint, data=payload)
        r.raise_for_status()
        return r.json()
