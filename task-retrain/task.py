import os
import requests
from requests.auth import HTTPBasicAuth
import boto3

s3 = boto3.client('s3')

auth = os.getenv('MACHINE_AUTH')
stack = os.getenv('StackName')
model_id = os.getenv('MODEL_ID')
prediction_id = os.getenv('PREDICTION_ID')
bucket = os.getenv('ASSET_BUCKET')
api = os.getenv('API_URL')

assert(stack)
assert(auth)
assert(model_id)
assert(prediction_id)
assert(api)

def get_pred(model_id, prediction_id):
    r = requests.get(api + '/v1/model/' + model_id + '/prediction/' + prediction_id, auth=HTTPBasicAuth('machine', auth))
    r.raise_for_status()

    pred = r.json()

    if pred['modelLink'] is None:
        raise Exception("Cannot retrain without modelLink")
    if pred['checkpointLink'] is None:
        raise Exception("Cannot retrain without checkpointLink")

    return pred

def get_asset(bucket, key):
    print('ok - downloading: ' + bucket + '/' + key)
    parsed = key.split('/')
    obj = s3.download_file(
        Filename='/tmp/' + parsed[len(parsed) - 1],
        Bucket=bucket,
        Key=key
    )



pred = get_pred(model_id, prediction_id)

get_asset(bucket, pred['modelLink'].replace(bucket + '/', ''))
get_asset(bucket, pred['checkpointLink'].replace(bucket + '/', ''))
