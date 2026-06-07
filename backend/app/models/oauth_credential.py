"""
OAuth credential storage.
Stores server-side Google OAuth tokens — one row per authenticated user.
The mobile app authenticates using a session_token returned at callback time.
"""

import secrets
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class OAuthCredential(Base):
    __tablename__ = "oauth_credentials"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: secrets.token_hex(16))
    user_email: Mapped[str] = mapped_column(String, unique=True, index=True)
    token: Mapped[str | None] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_uri: Mapped[str] = mapped_column(String, default="https://oauth2.googleapis.com/token")
    scopes: Mapped[list] = mapped_column(JSON, default=list)
    token_expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    session_token: Mapped[str] = mapped_column(
        String, unique=True, index=True, default=lambda: secrets.token_urlsafe(32)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
