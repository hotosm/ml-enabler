<h1 align=center>ML Enabler</h1>

<p align=center>A service that integrates ML models to applications like Tasking Manager.</p>

# **ML Enabler is now maintained and developed by Development Seed.**

* [Repository](https://github.com/developmentseed/ml-enabler)
* [Roadmap for version 3](https://github.com/developmentseed/ml-enabler/issues/4)


----
## Background

Machine Learning has proven to be very successful to make mapping fast with high quality. With a diverse set of models and tools, it is hard to integrate them to existing tools like Tasking Manager and iD. HOT is developing ml-enabler to enable AI-assist to existing mapping tools.

The API uses the following terms:
* **Model** --
A model is a machine learning model. With ml-enabler, we use the [TFService](https://www.tensorflow.org/tfx/tutorials/serving/rest_simple) convention of publishing models. This allows to spin up containers of the model for prediction and query the data for storage. For an example of a complete implementation, see Development Seed's [looking-glass](https://github.com/developmentseed/looking-glass-pub/). ml-enabler-api can store data from several versions of the same model.

* **Prediction** --
A prediction is a set of results from an ML Model for a bounding box (region) and at a specific tile level. For results that are not at tile level, the ml-enabler-cli will ensure this is aggregated a granular yet performant level. Predictions are tied to specific versions of a model.

* **Prediction tiles** --
Prediction tiles are the results of the prediction. The tiles are indexed using quadkeys for easy spatial search.

## Deploying

The CloudFormation template is designed to be AWS Account agnostic and will create all necessary resources with the exception of an SSL certificate (leave blank to disable https)

### Deploy Tools

The cloudformation template is designed to be deployed with [cfn-config](https://github.com/mapbox/cfn-config), or a cfn-config compatible client.
[OpenAddresses/Deploy](https://github.com/openaddresses/deploy) is a compatible client with a bunch of extra nice features.

### Paramaters

The following parameters have special considerations you should be aware of.

#### ContainerCpu & Container Memory

These values must be compatible with Fargate. See [Task CPU Limitations](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-cpu-memory-error.html)
for compatible values.

#### SSLCertificateIdentifier

The name of the SSL Cert as managed by AWS to use with the HTTPS ELB.
This value can be left blank to disable all HTTPS Load Balancing

## Using this API

See [API.md](/API.md)

## Development Setup

### Using Docker
1. Copy `example.env` to `ml_enabler.env`
1. Run `docker-compose build`
2. Run `docker-compose up`

### Manual
1. Create a virtualenv - `python3 -m venv venv`
3. Enable the virtualenv `./venv/bin/activate`
4. Install dependencies `pip install -r requirements.txt`
5. Setup the database:
  * Setup database. If you're on a Mac use Postgres.app, or use docker
  * Copy `example.env` to `ml_enabler.env` and add database configuration
  * Initialize tables `flask db upgrade`
6. Start the app
  * `export FLASK_APP="ml_enabler"`
  * `export FLASK_ENV="development"`
  * `flask run`

### Tests

1. Create a database for your tests:
  * `createdb ml_enabler_test`
  * Enabler postgis `echo 'CREATE EXTENSION postgis' | psql -d ml_enabler_test`
2. Run tests with `python3 -m unittest discover ml_enabler/tests/`

