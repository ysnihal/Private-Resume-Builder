"""
Optional password protection for the whole app - pages and API alike.

Only matters for a public deployment (Render). Locally, APP_PASSWORD is
left blank in .env, so this check is skipped entirely - nothing changes
about local development. Set APP_PASSWORD once deployed publicly, so a
stranger who finds the URL can't use your AI quota.
"""

import os
import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

_security = HTTPBasic(auto_error=False)


def require_app_password(credentials: HTTPBasicCredentials | None = Depends(_security)) -> None:
    app_password = os.getenv("APP_PASSWORD", "")
    if not app_password:
        return  # no password configured - e.g. local development

    # compare_digest avoids leaking the correct length/prefix via response timing.
    password_ok = credentials is not None and secrets.compare_digest(credentials.password, app_password)
    if not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password.",
            headers={"WWW-Authenticate": "Basic"},
        )
