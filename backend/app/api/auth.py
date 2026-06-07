"""
Google OAuth 2.0 flow for GDrive access.
Credentials are stored server-side — the mobile app only gets a session token.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.oauth_credential import OAuthCredential

router = APIRouter()

SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
]


def _build_flow() -> Flow:
    return Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
            }
        },
        scopes=SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
    )


@router.get("/login")
async def login():
    flow = _build_flow()
    auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
    return RedirectResponse(auth_url)


@router.get("/callback")
async def callback(code: str, state: str | None = None, db: AsyncSession = Depends(get_db)):
    flow = _build_flow()
    try:
        flow.fetch_token(code=code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    credentials = flow.credentials

    # Resolve user email from the id_token claims (populated by openid scope)
    id_info = credentials.id_token or {}
    user_email = id_info.get("email", "unknown@unknown")

    # Upsert credentials — one row per user
    result = await db.execute(
        select(OAuthCredential).where(OAuthCredential.user_email == user_email)
    )
    cred_row = result.scalar_one_or_none()

    if cred_row is None:
        cred_row = OAuthCredential(user_email=user_email)
        db.add(cred_row)

    cred_row.token = credentials.token
    cred_row.refresh_token = credentials.refresh_token or cred_row.refresh_token
    cred_row.token_uri = credentials.token_uri
    cred_row.scopes = list(credentials.scopes or SCOPES)
    cred_row.token_expiry = credentials.expiry

    await db.commit()
    await db.refresh(cred_row)

    return {"session_token": cred_row.session_token, "email": cred_row.user_email}
