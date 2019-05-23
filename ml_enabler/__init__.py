from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_restful import Api

db = SQLAlchemy()
migrate = Migrate()

# import models
from ml_enabler.models import * # noqa


def create_app(env=None):
    # create and configure the app
    app = Flask(__name__)
    app.config.from_object(f'ml_enabler.config.EnvironmentConfig')

    db.init_app(app)
    migrate.init_app(app, db)

    init_routes(app)
    return app


def init_routes(app):
    """ Initialize all API routes """

    api = Api(app)

    # import apis
    from ml_enabler.api.ml import StatusCheckAPI, MLModelAPI

    api.add_resource(StatusCheckAPI, '/')
    api.add_resource(MLModelAPI, '/model', endpoint="post", methods=['POST'])
    api.add_resource(MLModelAPI, '/model/<int:model_id>', methods=['DELETE', 'GET'])


if __name__ == '__main__':
    app = create_app()
    app.run()
