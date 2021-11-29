FROM tensorflow/tensorflow:2.1.0-gpu-py3

ENV SHELL /bin/bash
ENV HOME=/home/task
WORKDIR $HOME

COPY ./ $HOME/retrain
WORKDIR $HOME/retrain

RUN mkdir /ml
RUN mkdir /ml/models
RUN mkdir /ml/data
RUN mkdir /ml/checkpoint
RUN mkdir /tmp/tfrecords 


RUN apt-get update \
    && apt-get install -y git curl

RUN pip install -r requirements.txt

