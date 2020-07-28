from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_restful import Api
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

# import models
from ml_enabler.models import * # noqa
from ml_enabler.api import auth, task

def create_app(env=None, app_config='ml_enabler.config.EnvironmentConfig'):
    # create and configure the app
    app = Flask(__name__)
    app.config.from_object(app_config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    app.register_blueprint(auth.auth_bp)
    app.register_blueprint(task.task_bp)

    init_routes(app)
    return app


def init_routes(app):
    """ Initialize all API routes """

    api = Api(app)

    # import apis
    from ml_enabler.api.ml import StatusCheckAPI, MLModelAPI, GetAllModels, \
        PredictionAPI, PredictionUploadAPI, PredictionTileAPI, \
        GetAllPredictions, PredictionTileMVT, ImageryAPI, PredictionRetrain, \
        PredictionStackAPI, PredictionStacksAPI, PredictionInfAPI, MapboxAPI, MetaAPI, \
        PredictionExport, PredictionSingleAPI, PredictionValidity
    from ml_enabler.api.swagger import SwaggerDocsAPI

    api.add_resource(StatusCheckAPI,            '/')

    api.add_resource(MetaAPI,                   '/v1', methods=['GET'])

    api.add_resource(SwaggerDocsAPI,            '/v1/docs')

    api.add_resource(MapboxAPI,                 '/v1/mapbox', methods=['GET'])

    api.add_resource(PredictionStacksAPI,        '/v1/stacks', methods=['GET'])

    api.add_resource(GetAllModels,              '/v1/model/all', methods=['GET'])
    api.add_resource(MLModelAPI,                '/v1/model', endpoint="post", methods=['POST'])

    api.add_resource(MLModelAPI,                '/v1/model/<int:model_id>', methods=['DELETE', 'GET', 'PUT'])

    api.add_resource(ImageryAPI,                '/v1/model/<int:model_id>/imagery', methods=['POST', 'GET'])
    api.add_resource(ImageryAPI,                '/v1/model/<int:model_id>/imagery/<int:imagery_id>', endpoint="ImageryAPI.patch", methods=['PATCH'])
    api.add_resource(ImageryAPI,                '/v1/model/<int:model_id>/imagery/<int:imagery_id>', endpoint="ImageryAPI.delete", methods=['DELETE'])

    api.add_resource(PredictionAPI,             '/v1/model/<int:model_id>/prediction', methods=['POST', 'GET'])
    api.add_resource(GetAllPredictions,         '/v1/model/<int:model_id>/prediction/all', methods=['GET'])
    api.add_resource(PredictionSingleAPI,       '/v1/model/<int:model_id>/prediction/<int:prediction_id>', methods=['GET'])
    api.add_resource(PredictionAPI,             '/v1/model/<int:model_id>/prediction/<int:prediction_id>', endpoint="patch", methods=['PATCH'])
    api.add_resource(PredictionUploadAPI,       '/v1/model/<int:model_id>/prediction/<int:prediction_id>/upload', methods=['POST'])
    api.add_resource(PredictionStackAPI,        '/v1/model/<int:model_id>/prediction/<int:prediction_id>/stack', methods=['GET', 'POST', 'DELETE'])
    api.add_resource(PredictionInfAPI,          '/v1/model/<int:model_id>/prediction/<int:prediction_id>/stack/tiles', methods=['POST', 'GET', 'DELETE'])

    api.add_resource(PredictionValidity,        '/v1/model/<int:model_id>/prediction/<int:prediction_id>/validity', methods=['POST'])

    api.add_resource(PredictionExport,          '/v1/model/<int:model_id>/prediction/<int:prediction_id>/export', methods=['GET'])

    api.add_resource(PredictionRetrain,         '/v1/model/<int:model_id>/prediction/<int:prediction_id>/retrain', methods=['POST'])

    api.add_resource(PredictionTileAPI,         '/v1/model/<int:model_id>/prediction/<int:prediction_id>/tiles', endpoint="get", methods=['GET'])
    api.add_resource(PredictionTileMVT,         '/v1/model/<int:model_id>/prediction/<int:prediction_id>/tiles/<int:z>/<int:x>/<int:y>.mvt', methods=['GET'])

    api.add_resource(PredictionTileAPI,         '/v1/model/prediction/<int:prediction_id>/tiles', methods=['POST'])

if __name__ == '__main__':
    app = create_app()
    app.run()
