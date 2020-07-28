from flask import Blueprint, session
from flask_restful import request, current_app
from ml_enabler.utils import err
from ml_enabler.services.task_service import TaskService

task_bp = Blueprint(
    'task_bp', __name__
)

@task_bp.route('/v1/task', methods=['GET'])
def list():
    pred_id = request.args.get('pred_id')
    task_type = request.args.get('type')

    if pred_id is None:
        return err(400, 'pred_id param must be specified'), 400
    else:
        pred_id = int(pred_id)

    return TaskService.list(pred_id, task_type)

