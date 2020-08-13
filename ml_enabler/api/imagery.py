from flask import Blueprint, session
from flask_restful import request, current_app
from ml_enabler.utils import err
from ml_enabler.services.imagery_service import ImageryService
from ml_enabler.models.utils import NotFound, ImageryNotFound
import ml_enabler.config as CONFIG
from flask_login import login_required
from flask import jsonify

imagery_bp = Blueprint(
    'imagery_bp', __name__
)

@login_required
@imagery_bp.route('/v1/model/<int:model_id>/imagery', methods=['GET'])
def list(model_id):
    try:
        imagery = ImageryService.list(model_id)
        return jsonify(imagery), 200
    except ImageryNotFound:
        return err(404, "Imagery not found"), 404
    except Exception as e:
        error_msg = f'Unhandled error: {str(e)}'
        current_app.logger.error(error_msg)
        return err(500, error_msg), 500

@login_required
@imagery_bp.route('/v1/model/<int:model_id>/imagery/<int:imagery_id>', methods=['GET'])
def get(model_id, imagery_id):
    try:
        imagery = ImageryService.get(imagery_id)
        return imagery, 200
    except ImageryNotFound:
        return err(404, "Imagery not found"), 404
    except Exception as e:
        error_msg = f'Unhandled error: {str(e)}'
        current_app.logger.error(error_msg)
        return err(500, error_msg), 500

@login_required
@imagery_bp.route('/v1/model/<int:model_id>/imagery/<int:imagery_id>', methods=['PATCH'])
def patch(model_id, imagery_id):
    imagery = request.get_json();
    imagery_id = ImageryService.patch(model_id, imagery_id, imagery)

    return {
        "model_id": model_id,
        "imagery_id": imagery_id
    }, 200

@login_required
@imagery_bp.route('/v1/model/<int:model_id>/imagery/<int:imagery_id>', methods=['DELETE'])
def delete(model_id, imagery_id):
    ImageryService.delete(model_id, imagery_id)

    return "deleted", 200

@login_required
@imagery_bp.route('/v1/model/<int:model_id>/imagery', methods=['POST'])
def post(model_id):
    try:
        imagery = request.get_json()
        imagery_id = ImageryService.create(model_id, imagery)

        return {
            "model_id": model_id,
            "imagery_id": imagery_id
        }, 200
    except Exception as e:
        error_msg = f'Imagery Post: {str(e)}'
        current_app.logger.error(error_msg)
        return err(500, "Failed to save imagery source to DB"), 500

