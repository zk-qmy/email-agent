from flask import request
from flask_restful import Resource
from backend.services.mail_service import mail_service


class SignupResource(Resource):
    def post(self):
        data = request.get_json()
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        if not username or not email or not password:
            return {"error": "Missing required fields"}, 400

        result = mail_service.signup(username, email, password)
        if not result["success"]:
            return {"error": result["error"]}, 400

        return {"user_id": result["user_id"], "message": result["message"]}, 201


class LoginResource(Resource):
    def post(self):
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return {"error": "Missing email or password"}, 400

        result = mail_service.login(email, password)
        if not result["success"]:
            return {"error": result["error"]}, 401

        return {
            "user_id": result["user_id"],
            "username": result["username"],
            "email": result["email"],
        }, 200
