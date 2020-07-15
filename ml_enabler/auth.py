from flask import Blueprint, session
from flask_login import current_user, login_required, logout_user, login_user
from flask_restful import request, current_app
from ml_enabler.models.ml_model import User
from . import login_manager

auth_bp = Blueprint(
    'auth_bp', __name__
)

@auth_bp.route('/v1/user/login', methods=['POST'])
def login():
    payload = request.get_json()
    username = payload['username']
    password = payload['password']

    if username is None or username == "":
        return {
            "status": 400,
            "error": "No username provided"
        }, 400
    elif password is None or password == "":
        return {
            "status": 400,
            "error": "No password provided"
        }, 400

    try:
        user = User.query.filter_by(name=username).first()

        if user is None or not user.password_check(password):
            return { "status": 401, "error": "Invalid username or password" }, 401

        login_user(user)
        return { "status": 200, "message": "Logged In" }, 200
    except Exception as e:
        print(e)
        return { "status": 500, "error": "Internal Server Error" }, 500


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

