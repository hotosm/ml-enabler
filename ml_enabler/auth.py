from flask import Blueprint
from flask_login import current_user, login_required, logout_user
from . import login_manager

auth_bp = Blueprint(
    'auth_bp', __name__
)

@auth_bp.route('/v1/user/login', methods=['POST'])
def login():
    print("HERE")

@auth_bp.route('/v1/user/self', methods=['GET'])
def meta():
    print("HERE")

@auth_bp.route('/v1/user/logout', methods=['GET'])
def logout():
    logout_user()

    return {
        "status": 200,
        "message": "Logged Out"
    }, 200

@login_manager.user_loader
def user_load(user_id):
    if user_id is not None:
        return User.query.get(user_id)
    return None

