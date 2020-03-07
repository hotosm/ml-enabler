#!/usr/bin/env node

const unzipper = require('unzipper');
const request = require('request');
const Q = require('d3-queue').queue;
const mkdir = require('mkdirp').sync;
const pipeline = require('stream').pipeline;
const fs = require('fs');
const os = require('os');
const CP = require('child_process');
const path = require('path');
const AWS = require('aws-sdk');
const batch = new AWS.Batch({
    region: 'us-east-1'
});
const s3 = new AWS.S3({
    region: process.env.AWS_REGION
});

main();

async function main() {
    try {
        if (!process.env.MODEL) throw new Error('MODEL env var not set');
        if (!process.env.BATCH_ECR) throw new Error('BATCH_ECR env var not set');
        if (!process.env.AWS_ACCOUNT_ID) throw new Error('AWS_ACCOUT_ID env var not set');
        if (!process.env.AWS_REGION) throw new Error('AWS_REGION env var not set');
        if (!process.env.API_URL) throw new Error('API_URL env var not set');

        const tmp = os.tmpdir() + '/' + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15)

        const model = process.env.MODEL;

        mkdir(tmp + '/001');
        console.error(`ok - tmp dir: ${tmp}`);

        console.error(process.env);

        const model_id = get_model_id(model)
        const prediction_id = get_model_id(model)

        const links = {
            modelLink: model
        }

        if (process.env.AWS_BATCH_JOB_ID) {
            const logLink = await log_link();

            links.logLink = logLink;
        }

        await set_link(model_id, prediction_id, links)

        const dd = await dockerd();

        await get_zip(tmp, model);

        const finalLinks = await docker(tmp, model);

        await set_link(model_id, prediction_id, {
            saveLink: finalLinks.save,
            dockerLink: finalLinks.docker
        });

        dd.kill();
    } catch(err) {
        console.error(err);
        process.exit(1);
    }
}

function get_model_id(model) {
    // ml-enabler-test-1234-us-east-1/models/1/prediction/18/model.zip
    return parseInt(model.split('/')[2])
}

function get_prediction_id(model) {
    // ml-enabler-test-1234-us-east-1/models/1/prediction/18/model.zip
    return parseInt(model.split('/')[4])
}

function log_link() {
    return new Promise((resolve, reject) => {
        // Allow local runs

        batch.describeJobs({
            jobs: [ process.env.AWS_BATCH_JOB_ID ]
        }, (err, res) => {
            if (err) return reject(err);

            console.error(JSON.stringify(res.jobs[0])
            resolve(res.jobs[0].attempts[0].container.logStreamName)
        });
    });
}

function set_link(model, prediction, patch) {
    return new Promise((resolve, reject) => {
        console.error('ok - saving link state');

        request({
            method: 'PATCH',
            url: `${process.env.API_URL}/v1/model/${model}/prediction/${prediction}`,
            json: true,
            body: patch
        }, (err, res) => {
            if (err) return reject(err);

            return resolve(res);
        });
    });
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

function dockerd() {
    return new Promise((resolve, reject) => {
        console.error('ok - spawning dockerd');
        const dockerd = CP.spawn('dockerd');

        dockerd.stderr.on('data', (data) => {
            data = String(data);
            process.stdout.write(data);

            if (/API listen on/.test(data)) {
                setTimeout(() => {
                    return resolve(dockerd);
                }, 5000)
            }
        }).on('error', (err) => {
            return reject(err);
        });
    });
}

function docker(tmp, model) {
    return new Promise((resolve, reject) => {
        const tagged_model = model.split('/').splice(1).join('-').replace(/\-model\.zip/, '');

        try {
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

            const push = `${process.env.AWS_ACCOUNT_ID}.dkr.ecr.${process.env.AWS_REGION}.amazonaws.com/${process.env.BATCH_ECR}:${tagged_model}`;
            CP.execSync(`
                docker tag ${tag} ${push}
            `);

            CP.execSync(`
                $(aws ecr get-login --region us-east-1 --no-include-email)
            `)

            CP.execSync(`
                docker push ${push}
            `);
            console.error('ok - pushed image to AWS:ECR');

            CP.execSync(`
                docker save ${tag} | gzip > ${tmp}/docker-${tagged_model}.tar.gz
            `)
            console.error('ok - saved image to disk');
        } catch(err) {
            return reject(err);
        }

        s3.putObject({
            Bucket: model.split('/')[0],
            Key: model.split('/').splice(1).join('/').replace(/model\.zip/, `docker-${tagged_model}.tar.gz`),
            Body: fs.createReadStream(path.resolve(tmp, `docker-${tagged_model}.tar.gz`))
        }, (err, res) => {
            if (err) return reject(err);

            console.error('ok - saved image to s3');

            return resolve({
                docker: `${process.env.BATCH_ECR}:${tagged_model}`,
                save: model.split('/')[0] + '/' + model.split('/').splice(1).join('/').replace(/model\.zip/, `docker-${tagged_model}.tar.gz`)
            });
        });
    });
}

