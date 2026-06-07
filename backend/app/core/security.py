"""
FastAPI dependency for resolving Google OAuth credentials from a Bearer session token.
Usage:
    from app.core.security import get_credentials
    async def my_endpoint(creds: Credentials = Depends(get_credentials)):
        ...
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.oauth2.credentials import Credentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.oauth_credential import OAuthCredential

_bearer = HTTPBearer(auto_error=False)


async def get_credentials(
    auth: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> Credentials:
    """Return Google OAuth Credentials for the authenticated session.

    Raises 401 if the Bearer token is missing or invalid.
    """
    if auth is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Bearer token")

    result = await db.execute(
        select(OAuthCredential).where(OAuthCredential.session_token == auth.credentials)
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")

    return Credentials(
        token=row.token,
        refresh_token=row.refresh_token,
        token_uri=row.token_uri,
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=row.scopes,
        expiry=row.token_expiry,
    )
