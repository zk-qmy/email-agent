from flask import request
from flask_restful import Resource
from backend.services.mail_service import mail_service


class SendEmailResource(Resource):
    def post(self):
        data = request.get_json()
        sender_id = data.get("sender_id")
        recipient_email = data.get("recipient_email")
        subject = data.get("subject")
        body = data.get("body")

        if not all([sender_id, recipient_email, subject, body]):
            return {"error": "Missing required fields"}, 400

        result = mail_service.send_email(sender_id, recipient_email, subject, body)
        if not result["success"]:
            return {"error": result["error"]}, 400

        return {"email_id": result["email_id"], "message": result["message"]}, 201


class ReplyEmailResource(Resource):
    def post(self):
        data = request.get_json()
        sender_id = data.get("sender_id")
        parent_email_id = data.get("parent_email_id")
        body = data.get("body")

        if not all([sender_id, parent_email_id, body]):
            return {"error": "Missing required fields"}, 400

        result = mail_service.reply_email(sender_id, parent_email_id, body)
        if not result["success"]:
            return {"error": result["error"]}, 400

        return {"email_id": result["email_id"], "message": result["message"]}, 201


class InboxResource(Resource):
    def get(self):
        user_id = request.args.get("user_id", type=int)
        unread_only = request.args.get("unread", "false").lower() == "true"

        if not user_id:
            return {"error": "Missing user_id"}, 400

        emails = mail_service.get_inbox(user_id, unread_only)
        return {"emails": emails}, 200


class SentResource(Resource):
    def get(self):
        user_id = request.args.get("user_id", type=int)

        if not user_id:
            return {"error": "Missing user_id"}, 400

        emails = mail_service.get_sent(user_id)
        return {"emails": emails}, 200


class EmailDetailResource(Resource):
    def get(self, email_id):
        email = mail_service.get_email(email_id)
        if not email:
            return {"error": "Email not found"}, 404
        return {"email": email}, 200


class QueryEmailsResource(Resource):
    def post(self):
        data = request.get_json()
        user_id = data.get("user_id")

        if not user_id:
            return {"error": "Missing user_id"}, 400

        sender_email = data.get("sender_email")
        subject_kw = data.get("subject_kw")
        body_kw = data.get("body_kw")
        folder = data.get("folder")

        emails = mail_service.query_emails(user_id, sender_email, subject_kw, body_kw, folder)
        return {"emails": emails}, 200


class PollInboxResource(Resource):
    def get(self):
        user_id = request.args.get("user_id", type=int)
        last_check = request.args.get("last_check")

        if not user_id:
            return {"error": "Missing user_id"}, 400

        result = mail_service.poll_inbox(user_id, last_check)
        return result, 200


class MarkReadResource(Resource):
    def put(self):
        data = request.get_json()
        email_id = data.get("email_id")

        if not email_id:
            return {"error": "Missing email_id"}, 400

        result = mail_service.mark_read(email_id)
        if not result["success"]:
            return {"error": result["error"]}, 404

        return {"success": True}, 200
