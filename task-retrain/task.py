import os
import numpy as np
import requests
import boto3
import semver
import json

from requests.auth import HTTPBasicAuth
from requests_toolbelt.multipart.encoder import MultipartEncoder
from requests_toolbelt.utils import dump
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
    r = requests.get(api + '/v1/model/' + str(model_id) + '/prediction/' + str(prediction_id), auth=HTTPBasicAuth('machine', auth))
    r.raise_for_status()

    pred = r.json()
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

def get_versions(model_id):
    r = requests.get(api + '/v1/model/' + model_id + '/prediction/all', auth=HTTPBasicAuth('machine', auth))
    r.raise_for_status()
    preds = r.json()
    version_lst = []
    for pred_dict in preds:
        version_lst.append(pred_dict['version'])
    version_highest = str(max(map(semver.VersionInfo.parse, version_lst)))
    return version_highest

def post_pred(pred, version):
    data_pred = {
        'modelId': pred['modelId'],
        'version': version,
        'tileZoom': pred['tileZoom'],
        'infList': pred['infList'],
        'infType':  pred['infType'],
        'infBinary':  pred['infBinary'],
        'infSupertile': pred['infSupertile']
    }

    r = requests.post(api + '/v1/model/' + model_id + '/prediction',  json=data_pred, auth=HTTPBasicAuth('machine', auth))
    r.raise_for_status()
    print(r.status_code)
    pred = r.json()
    return pred['prediction_id']

def update_link(pred, link_type, zip_path):
    payload = {'type': link_type}
    print(payload)
    model_id = pred['modelId']
    print(model_id)
    prediction_id = pred['predictionsId']
    print(prediction_id)
    encoder = MultipartEncoder(fields={'file': ('filename', open(zip_path, 'rb'), 'application/zip')})
    print('/v1/model/' + str(model_id) + '/prediction/' + str(prediction_id) + '/upload')

    r = requests.post(api + '/v1/model/' + str(model_id) + '/prediction/' + str(prediction_id) + '/upload', params=payload,  
                        data = encoder, headers= {'Content-Type': encoder.content_type}, auth=HTTPBasicAuth('machine', auth))
    r.raise_for_status()

pred = get_pred(model_id, prediction_id)
if pred['modelLink'] is None:
    raise Exception("Cannot retrain without modelLink")
if pred['checkpointLink'] is None:
    raise Exception("Cannot retrain without checkpointLink")

zoom = pred['tileZoom']
supertile = pred['infSupertile']
version = pred['version']
inflist = pred['infList'].split(',')

if supertile: 
     x_feature_shape = [-1, 512, 512, 3]
else: 
    x_feature_shape = [-1, 256, 256, 3]

v = get_versions(model_id)

model = get_asset(bucket, pred['modelLink'].replace(bucket + '/', ''))
checkpoint = get_asset(bucket, pred['checkpointLink'].replace(bucket + '/', ''))

print(model)
print(checkpoint)

get_label_npz(model_id, prediction_id)

# download image tiles that match validated labels.npz file
download_img_match_labels(labels_folder='/tmp', imagery=imagery, folder='/tmp/tiles', zoom=zoom, supertile=supertile)

# create data.npz file that matchs up images and labels
make_datanpz(dest_folder='/tmp', imagery=imagery)

#get train and val number of samples 
d = np.load('/tmp/data.npz')
n_train_samps = d['y_train'].shape[0]
n_val_samps = d['y_val'].shape[0]

#convert data.npz into tf-records
create_tfr(npz_path='/tmp/data.npz', city='city')


# conduct re-training
train(tf_train_steps=200, tf_dir='/tmp/tfrecords.zip', 
       retraining_weights='/tmp/checkpoint.zip', 
       n_classes=len(inflist), class_names=inflist,  x_feature_shape=x_feature_shape, 
       n_train_samps=n_train_samps, n_val_samps=n_val_samps)

# increment model version
updated_version = str(increment_versions(version=v))
print(updated_version)


# post new pred
newpred_id = post_pred(pred=pred, version=updated_version)

newpred = get_pred(model_id, newpred_id)

# update tf-records zip
update_link(newpred, link_type='tfrecord', zip_path = '/tmp/tfrecords.zip')
print("tfrecords link updated")

# update model link
update_link(newpred, link_type='model', zip_path ='/ml/models.zip') 
print("models link updated")

# update checkpoint
update_link(newpred, link_type='checkpoint', zip_path = '/ml/checkpoint.zip')
print("checkpoint link updated")