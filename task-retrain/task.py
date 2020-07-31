import os
import requests
import boto3
import semver
import json

from requests.auth import HTTPBasicAuth
from requests_toolbelt.multipart.encoder import MultipartEncoder
from zipfile import ZipFile

from model import train
from generate_datanpz import download_img_match_labels, make_datanpz
from generate_tfrecords import create_tfr

s3 = boto3.client('s3')

# auth = os.getenv('MACHINE_AUTH')
# stack = os.getenv('StackName')
# model_id = os.getenv('MODEL_ID')
# prediction_id = os.getenv('PREDICTION_ID')
# bucket = os.getenv('ASSET_BUCKET')
# api = os.getenv('API_URL')
# imagery = os.getenv('TILE_ENDPOINT')

# assert(stack)
# assert(auth)
# assert(model_id)
# assert(prediction_id)
# assert(api)
# assert(imagery)

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
    #print(versions)
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

    pred = r.json()
    return pred['prediction_id']

def update_link(pred, link_type, zip_path='/Users/marthamorrissey/Documents/mle/models.zip'):
    payload = {'type': link_type}
    model_id = pred['modelId']
    prediction_id = pred['predictionsId']
    encoder = MultipartEncoder({'file': ('filename', open(zip_path, 'rb'), 'application/zip')})

    r = requests.post(api + '/v1/model/' + str(model_id) + '/prediction/' + str(prediction_id) + '/upload', params=payload,  
                        data = encoder, auth=HTTPBasicAuth('machine', auth))

pred = get_pred(model_id, prediction_id)
if pred['modelLink'] is None:
    raise Exception("Cannot retrain without modelLink")
if pred['checkpointLink'] is None:
    raise Exception("Cannot retrain without checkpointLink")

zoom = pred['tileZoom']
supertile = pred['infSupertile']
version = pred['version']

v = get_versions(model_id)

model = get_asset(bucket, pred['modelLink'].replace(bucket + '/', ''))
checkpoint = get_asset(bucket, pred['checkpointLink'].replace(bucket + '/', ''))

print(model)
print(checkpoint)

get_label_npz(model_id, prediction_id)

# #download image tiles that match validated labels.npz file
download_img_match_labels(labels_folder='/tmp', imagery=imagery, folder='/tmp/tiles', zoom=zoom, supertile=supertile)

#create data.npz file that matchs up images and labels
# TO-DO:fix arguments to pull from ml-enabler db
make_datanpz(dest_folder='/tmp', imagery=imagery)

#convert data.npz into tf-records
create_tfr(npz_path='/tmp/data.npz', city='city') #replace city with input from UI #/tmp/new_tfrecords 

#conduct re-training
train(tf_train_steps=10, tf_dir='/tmp/tfrecords.zip')
        retraining_weights='/tmp/checkpoint.zip')

#increpment model version
updated_version = str(increment_versions(version=v))
print(updated_version)


#post new pred
newpred_id = post_pred(pred=pred, version=updated_version)

newpred = get_pred(model_id, newpred_id)

#update tf-records zip
update_link(newpred, link_type='tfrecords', zip_path='/tmp/tfrecords.zip')

#update model link
update_link(newpred, link_type='model', zip_path='/ml/models.zip') 

#update checkpoint
update_link(newpred, link_type='checkpoint', zip_path='/ml/checkpoint_new.zip')