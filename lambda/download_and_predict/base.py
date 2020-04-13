"""
Lambda for downloading images, packaging them for prediction, sending them
to a remote ML serving image, and saving them
@author:Development Seed
"""

import json
from enum import Enum
from functools import reduce
from io import BytesIO
from base64 import b64encode
from urllib.parse import urlparse
from typing import Dict, List, NamedTuple, Callable, Optional, Tuple, Any, Iterator

import mercantile
from mercantile import Tile
import requests
import numpy as np

from download_and_predict.custom_types import SQSEvent

class ModelType(Enum):
    OBJECT_DETECT = 1
    CLASSIFICATION = 2

class DownloadAndPredict(object):
    """
    base object DownloadAndPredict implementing all necessary methods to
    make machine learning predictions
    """

    def __init__(self, imagery: str, mlenabler_endpoint: str, prediction_endpoint: str):
        super(DownloadAndPredict, self).__init__()

        self.imagery = imagery
        self.mlenabler_endpoint = mlenabler_endpoint
        self.prediction_endpoint = prediction_endpoint
        self.meta = {}

    def get_meta(self) -> ModelType:
        r = requests.get(self.prediction_endpoint + "/metadata")
        r.raise_for_status()

        self.meta = r.json()

        inputs = self.meta["metadata"]["signature_def"]["signature_def"]["serving_default"]["inputs"]

        # Object Detection Model
        if inputs.get("inputs") is not None:
            return ModelType.OBJECT_DETECT

        # Chip Classification Model
        else:
            return ModelType.CLASSIFICATION

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


    def get_prediction_payload(self, tiles:List[Tile], model_type: ModelType) -> Tuple[List[Tile], Dict[str, Any]]:
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

        instances = []
        if model_type == ModelType.CLASSIFICATION:
            instances = [dict(image_bytes=dict(b64=self.b64encode_image(img))) for img in images]
        else:
            instances = [dict(inputs=dict(b64=self.b64encode_image(img))) for img in images]

        payload = {
            "instances": instances
        }

        return (list(tile_indices), payload)

    def cl_post_prediction(self, payload: Dict[str, Any], tiles: List[Tile], prediction_id: str, inferences: List[str]) -> Dict[str, Any]:
        payload = json.dumps(payload)
        r = requests.post(self.prediction_endpoint + ":predict", data=payload)
        print(r.text)
        r.raise_for_status()

        preds = r.json()["predictions"]
        pred_list = [];

        for i in range(len(tiles)):
            pred_dict = {}

            for j in range(len(preds[i])):
                pred_dict[inferences[j]] = preds[i][j]

            pred_list.append({
                "quadkey": mercantile.quadkey(tiles[i].x, tiles[i].y, tiles[i].z),
                "predictions": pred_dict,
                "prediction_id": prediction_id
            })

        return {
            "predictionId": prediction_id,
            "predictions": pred_list
        }

    def od_post_prediction(self, payload: str, tiles: List[Tile], prediction_id: str) -> Dict[str, Any]:
        pred_list = [];

        for i in range(len(tiles)):
            r = requests.post(self.prediction_endpoint + ":predict", data=json.dumps({
                "instances": [ payload["instances"][i] ]
            }))

            print(r.text)
            r.raise_for_status()

            preds = r.json()["predictions"]

            print(pres)

            if len(preds) == 0.0:
                break
            elif preds[0]["num_detections"] == 0.0:
                break

            boxes = preds[0]['detection_boxes']
            scores = preds[0]['detection_scores']
            bboxes = (np.squeeze(boxes)[np.squeeze(scores) > .5] * 256).astype(int)
            bboxes_ls = bboxes.tolist()

            for j, bbox in enumerate(bboxes_ls):
                bbox = self.tf_bbox_geo(bbox, tiles[i])
                score = predl[0]["detection_scores"][j]

                print(bbox)

                pred_list.append({
                    "prediction_id": prediction_id
                })

        return {
            "predictionId": prediction_id,
            "predictions": pred_list
        }

    def cl_save_prediction(self, prediction_id: str, payload):
        url = self.mlenabler_endpoint + "/v1/model/prediction/" + prediction_id + "/tiles"
        r = requests.post(url, json=payload)
        r.raise_for_status()

        print(r.text)

        return True

    def tf_bbox_geo(self, bbox, tile):
        pred = [bbox[1], bbox[0], bbox[3], bbox[2]]
        b = mercantile.bounds(tile.x, tile.y, tile.z)
        # Affine Transform
        width = b[2] - b[0]
        height = b[3] - b[1]
        a = affine.Affine(width / 256, 0.0, b[0], 0.0, (0 - height / 256), b[3])
        a_lst = [a.a, a.b, a.d, a.e, a.xoff, a.yoff]
        geographic_bbox = shapely.affinity.affine_transform(geometry.box(*pred), a_lst)

        return geographic_bbox

