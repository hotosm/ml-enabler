FROM ubuntu:19.10

RUN rm /bin/sh && ln -s /bin/bash /bin/sh
ENV SHELL /bin/bash

RUN apt-get update -y \
    && apt-get install -y git curl aws-cli docker.io \
    && curl 'https://nodejs.org/dist/v13.8.0/node-v13.8.0-linux-x64.tar.gz' | tar -xzv \
    && cp ./node-v13.8.0-linux-x64/bin/node /usr/bin/ \
    && ./node-v13.8.0-linux-x64/bin/npm install -g npm \
    && npm install -g yarn

WORKDIR /usr/local/src/batch
ADD . /usr/local/src/batch

RUN yarn install
