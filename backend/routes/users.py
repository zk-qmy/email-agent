from fastapi import APIRouter, Query
from backend.services.mail_service import MailService

mail_service = MailService()
router = APIRouter()


@router.get("/search-users")
async def search_users(q: str = Query(..., min_length=1)):
    users = mail_service.search_users(q)
    return {"users": users}