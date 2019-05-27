# ml-enabler

A service that integrates ML models to applications like Tasking Manager. _work in progress_

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

