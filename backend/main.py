import os
from flask import Flask
from flask_restful import Api
from flask_cors import CORS
from backend.database import init_db, seed_data
from backend.routes.auth import SignupResource, LoginResource
from backend.routes.email import (
    SendEmailResource,
    ReplyEmailResource,
    InboxResource,
    SentResource,
    EmailDetailResource,
    QueryEmailsResource,
    PollInboxResource,
    MarkReadResource,
)


def create_app():
    app = Flask(__name__)
    CORS(app)

    app.config["DATABASE_URL"] = os.getenv("DATABASE_URL", "sqlite:///email-agent.db")

    api = Api(app)

    api.add_resource(SignupResource, "/api/auth/signup")
    api.add_resource(LoginResource, "/api/auth/login")
    api.add_resource(SendEmailResource, "/api/emails/send")
    api.add_resource(ReplyEmailResource, "/api/emails/reply")
    api.add_resource(InboxResource, "/api/emails/inbox")
    api.add_resource(SentResource, "/api/emails/sent")
    api.add_resource(EmailDetailResource, "/api/emails/<int:email_id>")
    api.add_resource(QueryEmailsResource, "/api/emails/query")
    api.add_resource(PollInboxResource, "/api/emails/poll")
    api.add_resource(MarkReadResource, "/api/emails/mark_read")

    return app


app = create_app()

if __name__ == "__main__":
    init_db()
    seed_data()
    port = int(os.getenv("EMAIL_BACKEND_PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
