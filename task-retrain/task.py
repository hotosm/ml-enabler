import os
import requests

auth = os.getenv('MACHINE_AUTH')
prediction_id = os.getenv('PREDICTION_ID')
mlenabler_endpoint = os.getenv('MLENABLER_ENDPOINT')

assert(auth)
assert(prediction_id)
assert(mlenabler_endpoint)
