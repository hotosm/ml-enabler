#!/usr/bin/env bash
# based on github.com/mapbox/lambda-cfn

# ./util/upload-lambda lambda-directory bucket/prefix

GITSHA=$(git rev-parse HEAD)
echo "ok - ${GITSHA}"

make -B build

aws s3 cp ./package.zip s3://devseed-artifacts/ml-enabler/lambda-${GITSHA}.zip

rm ./package.zip
