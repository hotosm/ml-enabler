from flask import Blueprint, session
from flask_restful import request, current_app
from ml_enabler.utils import err
from ml_enabler.services.integration_service import IntegrationService
from ml_enabler.models.utils import NotFound, IntegrationNotFound
import ml_enabler.config as CONFIG
from flask_login import login_required
from flask import jsonify

integration_bp = Blueprint(
    'integration_bp', __name__
)

@login_required
@integration_bp.route('/v1/model/<int:model_id>/integration', methods=['GET'])
def list(model_id):
    try:
        integration = IntegrationService.list(model_id)
        return jsonify(integration), 200
    except IntegrationNotFound:
        return err(404, "Integration not found"), 404
    except Exception as e:
        error_msg = f'Unhandled error: {str(e)}'
        current_app.logger.error(error_msg)
        return err(500, error_msg), 500

@login_required
@integration_bp.route('/v1/model/<int:model_id>/integration/<int:integration_id>', methods=['GET'])
def get(model_id, integration_id):
    try:
        integration = IntegrationService.get(integration_id)
        return integration, 200
    except IntegrationNotFound:
        return err(404, "Integration not found"), 404
    except Exception as e:
        error_msg = f'Unhandled error: {str(e)}'
        current_app.logger.error(error_msg)
        return err(500, error_msg), 500

@login_required
@integration_bp.route('/v1/model/<int:model_id>/integration/<int:integration_id>', methods=['PATCH'])
def patch(model_id, integration_id):
    integration = request.get_json();
    integration_id = IntegrationService.patch(model_id, integration_id, integration)

    return {
        "model_id": model_id,
        "integration_id": integration_id
    }, 200

@login_required
@integration_bp.route('/v1/model/<int:model_id>/integration/<int:integration_id>', methods=['DELETE'])
def delete(model_id, integration_id):
    IntegrationService.delete(model_id, integration_id)

    return { "status": "deleted" }, 200

@login_required
@integration_bp.route('/v1/model/<int:model_id>/integration', methods=['POST'])
def post(model_id):
    try:
        integration = request.get_json()
        integration_id = IntegrationService.create(model_id, integration)

        return {
            "model_id": model_id,
            "integration_id": integration_id
        }, 200
    except Exception as e:
        error_msg = f'Integration Post: {str(e)}'
        current_app.logger.error(error_msg)
        return err(500, "Failed to save integration source to DB"), 500

@login_required
@integration_bp.route('/v1/model/<int:model_id>/integration/<int:integration_id>', methods=['POST'])
def use(model_id, integration_id):
    integration_data = request.get_json();

    return {
        "status": "created"
    }, 200
