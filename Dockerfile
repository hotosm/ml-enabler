FROM python:3.6.3-jessie

EXPOSE 5000

ENV HOME=/home/hot
WORKDIR $HOME

COPY ./ $HOME/ml-enabler
WORKDIR $HOME/ml-enabler
RUN \ 
  pip install gunicorn; \
  pip install -r requirements.txt

CMD gunicorn --bind 0.0.0.0:5000 --timeout 120 'ml_enabler:create_app()'
