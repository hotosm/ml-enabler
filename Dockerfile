FROM python:3.6.3-jessie

EXPOSE 5000

ENV HOME=/home/hot
WORKDIR $HOME

COPY ./ $HOME/ml-enabler
WORKDIR $HOME/ml-enabler
RUN \
  pip install gunicorn; \
  pip install -r requirements.txt

CMD flask db upgrade \
    && echo "CREATE DATABASE ${POSTGRES_DB}" | psql postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_ENDPOINT}:${POSTGRES_PORT} || true \
    && echo "CREATE EXTENSION POSTGRES" | psql postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_ENDPOINT}:${POSTGRES_PORT}/${POSTGRES_DB} \
    && gunicorn --bind 0.0.0.0:5000 --timeout 120 'ml_enabler:create_app()'
