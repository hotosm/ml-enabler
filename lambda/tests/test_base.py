import pytest
from mercantile import Tile

from download_and_predict.base import DownloadAndPredict

def test_get_tiles():
    # create a class with fake environment variables
    dap = DownloadAndPredict(
        imagery='https://example.com/{z}/{x}/{y}.png',
        db='postgres://usr:pw@host:port/database',
        prediction_endpoint='https://myloadbalancer.com/v1/models/ml:predict'
    )

    # create an example SQS event which invokes a lambda
    event = { 'Records': [ { "body": '{ "x": 4, "y": 5, "z":3 }' }] }

    tiles = dap.get_tiles(event)
    fixture_tiles = [Tile(x=4, y=5, z=3)]

    assert(tiles == fixture_tiles)
