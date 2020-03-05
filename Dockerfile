FROM alpine:3.11

EXPOSE 5000

ENV HOME=/home/hot
ENV FLASK_APP=ml_enabler
WORKDIR $HOME

COPY ./ $HOME/ml-enabler
WORKDIR $HOME/ml-enabler

RUN apk add postgresql-client postgresql-dev curl nginx nodejs npm yarn python3 py3-pip

RUN cd web \
    && yarn install \
    && yarn build \
    && cd ..

RUN \
  pip3 install gunicorn; \
  pip3 install -r requirements.txt

RUN cp ./cloudformation/nginx.conf /etc/nginx/sites-enabled/default

CMD service nginx restart \
    && echo "CREATE DATABASE ${POSTGRES_DB}" | psql postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_ENDPOINT}:${POSTGRES_PORT} || true \
    && echo "CREATE EXTENSION POSTGIS" | psql postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_ENDPOINT}:${POSTGRES_PORT}/${POSTGRES_DB} || true \
    && flask db upgrade || true \
    && gunicorn --bind 0.0.0.0:4000 --timeout 120 'ml_enabler:create_app()'
