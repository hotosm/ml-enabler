
FROM python:3.6.3-jessie

EXPOSE 80
EXPOSE 443

RUN \
	apt-get update; \
	apt-get install -y postgresql-client vim git

ENV HOME=/home/hot
WORKDIR $HOME

COPY ./ $HOME/ml-enabler
WORKDIR $HOME/ml-enabler
RUN \ 
  pip install gunicorn; \
  pip install -r requirements.txt

CMD echo 'done!'