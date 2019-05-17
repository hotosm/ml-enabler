# ml-enabler

A service that integrates ML models to applications like Tasking Manager. _work in progress_

## Setup

1. Git clone
2. Create a virtualenv - `python3 -m venv venv`
3. Enable the virtualenv `./venv/bin/activate`
4. Install dependencies `pip install -r requirements.txt`
5. Setup Database:
  * Setup database. If you're on a mac use Postgres.app, or use docker (coming soon)
  * Copy example.env to `ml_enabler.env` and add database configurations
  * Initialize tables `flask db upgrade`
6. Start the app 
  * `export FLASK_APP="ml_enabler"`
  * `export FLASK_ENV="development"`
  * `flask run`