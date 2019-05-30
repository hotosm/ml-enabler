from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_restful import Api

db = SQLAlchemy()
migrate = Migrate()

# import models
from ml_enabler.models import * # noqa


def create_app(env=None, app_config='ml_enabler.config.EnvironmentConfig'):
    # create and configure the app
    app = Flask(__name__)
    app.config.from_object(app_config)

    db.init_app(app)
    migrate.init_app(app, db)

    init_routes(app)
    return app


def init_routes(app):
    """ Initialize all API routes """

    api = Api(app)

    # import apis
    from ml_enabler.api.ml import StatusCheckAPI, MLModelAPI, GetAllModels, PredictionAPI
    from ml_enabler.api.swagger import SwaggerDocsAPI

    api.add_resource(SwaggerDocsAPI, '/docs')
    api.add_resource(StatusCheckAPI, '/')
    api.add_resource(GetAllModels, '/model/all', methods=['GET'])
    api.add_resource(MLModelAPI, '/model', endpoint="post", methods=['POST'])
    api.add_resource(MLModelAPI, '/model/<int:model_id>', methods=['DELETE', 'GET', 'PUT'])
    api.add_resource(PredictionAPI, '/prediction/<int:model_id>', methods=['POST'])


if __name__ == '__main__':
    app = create_app()
    app.run()
