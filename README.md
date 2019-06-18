# ml-enabler

A service that integrates ML models to applications like Tasking Manager. _work in progress_

## Background
Machine Learning has proven to be very successful to make mapping fast with high quality. With a diverse set of models and tools, it is hard to integrate them to existing tools like Tasking Manager and iD. HOT is developing ml-enabler to enable AI-assist to existing mapping tools.

ml-enabler is two projects:
1. ml-enabler-api (this repo) - Storage and API to hold tile level ML prediction data.
2. ml-enabler-cli ([repo](https://github.com/hotosm/ml-enabler-cli)) - CLI for interacting with models and subscribe them to the ml-enabler-api

The API uses the following terms:
* Model
A model is a machine learning model. With ml-enabler, we use the [TFService](https://www.tensorflow.org/tfx/tutorials/serving/rest_simple) convention of publishing models. This allows to spin up containers of the model for prediction and query the data for storage. For an example of a complete implementation, see Development Seed's [looking-glass](https://github.com/developmentseed/looking-glass-pub/). ml-enabler-api can store data from several versions of the same model.

* Prediction
A prediction is a set of results from an ML Model for a bounding box (region) and at a specific tile level. For results that are not at tile level, the ml-enabler-cli will ensure this is aggregated a granular yet performant level. Predictions are tied to specific versions of a model.

* Prediction tiles
Prediction tiles are the results of the prediction. The tiles are indexed using quadkeys for easy spatial search.

## Using this API

See [API.md](/API.md)

## Setup

### Using Docker
0. Create ml_enabler.env
1. docker-compose build
2. docker-compose up

### Manual setup
1. Create a virtualenv - `python3 -m venv venv`
3. Enable the virtualenv `./venv/bin/activate`
4. Install dependencies `pip install -r requirements.txt`
5. Setup Database:
  * Setup database. If you're on a mac use Postgres.app, or use docker
  * Copy example.env to `ml_enabler.env` and add database configurations
  * Initialize tables `flask db upgrade`
6. Start the app 
  * `export FLASK_APP="ml_enabler"`
  * `export FLASK_ENV="development"`
  * `flask run`

### Tests

Create a database for your tests:

    createdb ml_enabler_test
    echo 'CREATE EXTENSION postgis' | psql -d ml_enabler_test

Run tests with:

    python3 -m unittest discover ml_enabler/tests/

