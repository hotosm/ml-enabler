import os
import requests
import boto3
import semver

from requests.auth import HTTPBasicAuth
from zipfile import ZipFile

from model import train
from generate_datanpz import download_img_match_labels, make_datanpz
from generate_tfrecords import create_tfr

s3 = boto3.client('s3')

auth = os.getenv('MACHINE_AUTH')
stack = os.getenv('StackName')
model_id = os.getenv('MODEL_ID')
prediction_id = os.getenv('PREDICTION_ID')
bucket = os.getenv('ASSET_BUCKET')
api = os.getenv('API_URL')
imagery = os.getenv('TILE_ENDPOINT')

assert(stack)
assert(auth)
assert(model_id)
assert(prediction_id)
assert(api)
assert(imagery)

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

    dirr =  parsed[len(parsed) - 1].replace('.zip', '')
    with ZipFile('/tmp/' + parsed[len(parsed) - 1], 'r') as zipObj:
       # Extract all the contents of zip file in different directory
          zipObj.extractall('/tmp/' + dirr)

    return '/tmp/' + dirr

def get_label_npz(model_id, prediction_id):
    payload = {'format':'npz', 'inferences':'all', 'threshold': 0}
    r = requests.get(api + '/v1/model/' + model_id + '/prediction/' + prediction_id + '/export', params=payload,
                    auth=HTTPBasicAuth('machine', auth))
    r.raise_for_status()
    with open('/tmp/labels.npz', 'wb') as f:
        f.write(r.content)
    return f

def increment_versions(version):
    v = semver.VersionInfo.parse(version)
    return v.bump_minor()

def post_pred(pred, version):
    data = {
        'modelId': pred['modelId'],
        'version': version,
        'tileZoom': pred['tileZoom'],
        'infList': pred['infList'],
        'infType':  pred['infType'],
        'infBinary':  pred['infBinary'],
        'infSupertile': pred['infSupertile']
    }

    r = requests.post(api + '/v1/model/' + model_id + '/prediction/' + prediction_id, auth=HTTPBasicAuth('machine', auth), data = data)

pred = get_pred(model_id, prediction_id)
#print(pred)
print(pred.keys())
zoom = pred['tileZoom']
supertile = pred['infSupertile']
version = pred['version']

model = get_asset(bucket, pred['modelLink'].replace(bucket + '/', ''))
checkpoint = get_asset(bucket, pred['checkpointLink'].replace(bucket + '/', ''))

print(model)
print(checkpoint)

get_label_npz(model_id, prediction_id)

#download image tiles that match validated labels.npz file
download_img_match_labels(labels_folder='/tmp', imagery=imagery, folder='/tmp/tiles', zoom=zoom, supertile=supertile)

#create data.npz file that matchs up images and labels

# TO-DO:fix arguments to pull from ml-enabler db
make_datanpz(dest_folder='/tmp', imagery=imagery)

#convert data.npz into tf-records
create_tfr(npz_path='/tmp/data.npz',
            dest_folder='/tmp/', city='city') #replace city with input from UI

#conduct re-training
train(tf_train_steps=10, tf_train_data_dir='/tmp', tf_val_data_dir='/tmp')

#increpment model version
updated_version = increment_versions(version=version)


#post new pred
post_pred(pred=pred, version=updated_version)
