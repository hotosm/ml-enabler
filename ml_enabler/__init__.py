# flake8: noqa
import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

# import models
from ml_enabler.models import *

def create_app(env=None):
    # create and configure the app
    app = Flask(__name__)
    app.config.from_object(f'ml_enabler.config.EnvironmentConfig')

    db.init_app(app)
    migrate.init_app(app, db)

    # a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    return app
