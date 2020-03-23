#!/usr/bin/env bash
# based on github.com/mapbox/lambda-cfn

# ./util/upload-lambda lambda-directory bucket/prefix

GITSHA=$(git rev-parse HEAD)
echo "ok - ${GITSHA}"

python3 -m venv v-env
source v-env/bin/activate
pip install .

zip -qr /tmp/${GITSHA}.zip *

aws s3 cp /tmp/${GITSHA}.zip s3://devseed-artifacts/ml-enabler/lambda-${GITSHA}.zip

rm /tmp/${GITSHA}.zip
