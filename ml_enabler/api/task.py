from flask import Blueprint, session
from flask_restful import request, current_app
from ml_enabler.utils import err
from ml_enabler.services.task_service import TaskService
from ml_enabler.models.utils import NotFound
import ml_enabler.config as CONFIG

task_bp = Blueprint(
    'task_bp', __name__
)

@task_bp.route('/v1/task', methods=['GET'])
def list():
    if CONFIG.EnvironmentConfig.ENVIRONMENT != "aws":
        return err(501, "stack must be in 'aws' mode to use this endpoint"), 501

    pred_id = request.args.get('pred_id')
    task_type = request.args.get('type')

    if pred_id is None:
        return err(400, 'pred_id param must be specified'), 400
    else:
        pred_id = int(pred_id)

    try:
        return TaskService.list(pred_id, task_type)
    except NotFound:
        return err(404, "task not found"), 404
    except Exception as e:
        error_msg = f'Unhandled error: {str(e)}'
        current_app.logger.error(error_msg)
        return err(500, error_msg), 500

@task_bp.route('/v1/task/<int:task_id>', methods=['GET'])
def get(task_id):
    if CONFIG.EnvironmentConfig.ENVIRONMENT != "aws":
        return err(501, "stack must be in 'aws' mode to use this endpoint"), 501

    try:
        return TaskService.get(task_id)
    except NotFound:
        return err(404, "task not found"), 404
    except Exception as e:
        error_msg = f'Unhandled error: {str(e)}'
        current_app.logger.error(error_msg)
        return err(500, error_msg), 500

@task_bp.route('/v1/task/<int:task_id>/logs', methods=['GET'])
def logs(task_id):
    if CONFIG.EnvironmentConfig.ENVIRONMENT != "aws":
        return err(501, "stack must be in 'aws' mode to use this endpoint"), 501

    try:
        return TaskService.logs(task_id)
    except NotFound:
        return err(404, "task not found"), 404
    except Exception as e:
        error_msg = f'Unhandled error: {str(e)}'
        current_app.logger.error(error_msg)
        return err(500, error_msg), 500

@task_bp.route('/v1/task/<int:task_id>', methods=['DELETE'])
def delete(task_id):
    if CONFIG.EnvironmentConfig.ENVIRONMENT != "aws":
        return err(501, "stack must be in 'aws' mode to use this endpoint"), 501

    try:
        return TaskService.delete(task_id)
    except NotFound:
        return err(404, "task not found"), 404
    except Exception as e:
        error_msg = f'Unhandled error: {str(e)}'
        current_app.logger.error(error_msg)
        return err(500, error_msg), 500
