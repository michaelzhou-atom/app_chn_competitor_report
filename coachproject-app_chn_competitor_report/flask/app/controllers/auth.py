import os
import datetime
import jwt
from flask import Blueprint, jsonify, request, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from ..models import Auth
from ..helpers import api_key_required

auth = Blueprint("auth", __name__, url_prefix="/backend/auth")


@auth.route("/login", methods=["POST"])
def login():

    # get credentials and role from request body
    # fetch the user with username where the role:=given_role
    # authenticate the user by matching the password
    # create jwt
    # send token in response

    request_body = request.json
    username = request_body["username"]
    password = request_body["password"]

    try:

        creds = Auth.get_creds(username)
        role = creds.role

        if (
            username == creds.username
            and check_password_hash(creds.password, password)
            and role
        ):
            # Create JWT token
            expiration_time = datetime.datetime.utcnow() + datetime.timedelta(
                seconds=current_app.config["JWT_EXP_DURATION"]
            )
            token = jwt.encode(
                {"user": username, "role": role, "exp": expiration_time},
                current_app.config["JWT_SECRET"],
                algorithm="HS256",
            )
            return jsonify({"token": token, "role": role})

        return jsonify({"message": "Unable to authenticate!"}), 401

    except Exception as e:
        return jsonify({"message": "Unable to authenticate!"}), 401


@auth.route("/register", methods=["POST"])
@api_key_required
def create():
    request_body = request.json
    username = request_body["username"]
    password = request_body["password"]
    role = request_body["role"]
    
    try:
        Auth.insert_user(username, generate_password_hash(password), role)
        return jsonify({"data": []})
    except Exception as e:
        return jsonify({"message": "could not create user", "error": str(e)})


@auth.route("/change-password", methods=["POST"])
@api_key_required
def update():
    request_body = request.json
    username = request_body["username"]
    password = request_body["password"]
    role = request_body["role"]

    try:
        Auth.update_password(username, generate_password_hash(password), role)
        return jsonify({"data": []})
    except Exception as e:
        return jsonify({"message": "could not update password", "error": str(e)})

