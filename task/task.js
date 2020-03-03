#!/usr/bin/env node

const Q = require('d3-queue').queue;
const mkdir = require('mkdirp').sync;
const fs = require('fs');
const os = require('os');
const CP = require('child_process');
const tmp = os.tmpdir() + '/' + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15)
const path = require('path');

main();

async function main() {
    if (!process.env.MODEL) throw new Error('No MODEL env var found');

    const model = process.env.MODEL;

    mkdir(tmp + '/001');
    console.error(`ok - tmp dir: ${tmp}`);

    try {
        await get_zip();

        await docker();

        await push();
    } catch(err) {
        throw err;
    }
}

function get_zip() {

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

