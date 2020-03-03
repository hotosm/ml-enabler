#!/usr/bin/env node

const unzipper = require('unzipper');
const Q = require('d3-queue').queue;
const mkdir = require('mkdirp').sync;
const pipeline = require('stream').pipeline;
const fs = require('fs');
const os = require('os');
const CP = require('child_process');
const path = require('path');
const AWS = require('aws-sdk');
const s3 = new AWS.S3({
    region: 'us-east-1'
});

main();

async function main() {
    try {
        if (!process.env.MODEL) throw new Error('No MODEL env var found');

        const tmp = os.tmpdir() + '/' + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15)

        const model = process.env.MODEL;

        mkdir(tmp + '/001');
        console.error(`ok - tmp dir: ${tmp}`);

        await get_zip(tmp, model);

        await docker();

        await push();
    } catch(err) {
        console.error(err);
        process.exit(1);
    }
}

function get_zip(tmp, model) {
    return new Promise((resolve, reject) => {
        console.error(`ok - fetching ${model}`);

        const loc = path.resolve(tmp, 'model.zip');

        pipeline(
            s3.getObject({
                Bucket: model.split('/')[0],
                Key: model.split('/').splice(1).join('/')
            }).createReadStream(),
            unzipper.Extract({ path: tmp }),
        (err, res) => {
            if (err) return reject(err);

            console.error(`ok - saved: ${loc}`);

            return resolve(loc);
        });
    });
}

function docker(err, res) {
    if (err) throw err;

    console.error('ok - pulling tensorflow/serving docker image');
    CP.execSync(`
        docker pull tensorflow/serving
    `);

    // Ignore errors, these are to ensure the next commands don't err
    try {
        CP.execSync(`
            docker kill serving_base
        `);
    } catch(err) {
        console.error('ok - no old task to stop');
    }

    try {
        CP.execSync(`
            docker rm serving_base
        `);
    } catch(err) {
        console.error('ok - no old image to remove');
    }

    CP.execSync(`
        docker run -d --name serving_base tensorflow/serving
    `);

    CP.execSync(`
        docker cp ${tmp}/ serving_base:/models/default/ \
    `);

    const tag = `developmentseed/default:${Math.random().toString(36).substring(2, 15)}`;

    CP.execSync(`
        docker commit --change "ENV MODEL_NAME default" serving_base ${tag}
    `);

    console.error(`ok - docker: ${tag}`);

    console.error();
    console.error(`ok - Run with docker run -p 8501:8501 -t ${tag}`);
    console.error();

}

