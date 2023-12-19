"""Secret dependency.
"""
import secrets
import uuid
from typing import Optional

from fastapi import Security
from fastapi.security import APIKeyHeader
from starlette.exceptions import HTTPException
from starlette.status import HTTP_403_FORBIDDEN

from rd_syncrr.logging import logger
from rd_syncrr.settings import settings


class GhostLoadedSecret:
    """Ghost-loaded secret handler"""

    def __init__(self) -> None:
        self._secret = None

    @property
    def value(self):
        if self._secret:
            return self._secret

        else:
            self._secret = self.get_secret_value()
            return self.value

    def get_secret_value(self):
        """Get secret value from environment variable or generate a new one."""
        if settings.security_secret:
            try:
                secret_value = settings.security_secret
            except KeyError:
                secret_value = str(uuid.uuid4())
                logger.warning(
                    "ENVIRONMENT VARIABLE 'RD_SYNCRR_SECURITY_SECRET' FORMAT INCORECT\n"
                    "\tGenerated a single-use secret key for this session:\n"
                    f"\t{secret_value=}"
                )
        else:
            secret_value = str(uuid.uuid4())
            logger.warning(
                "ENVIRONMENT VARIABLE 'RD_SYNCRR_SECURITY_SECRET' NOT FOUND\n"
                "\tGenerated a single-use secret key for this session:\n"
                f"\t{secret_value=}"
            )

        return secret_value


secret = GhostLoadedSecret()

SECRET_KEY_NAME = "secret-key"  # noqa: S105

secret_header = APIKeyHeader(
    name=SECRET_KEY_NAME, scheme_name="Secret header", auto_error=False
)


async def secret_based_security(header_param: Optional[str] = Security(secret_header)):
    """
    Args:
        header_param: parsed header field secret_header

    Returns:
        True if the authentication was successful

    Raises:
        HTTPException if the authentication failed
    """

    if not header_param:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="secret_key must be passed as a header field",
        )

    # We simply return True if the given secret-key has the right value
    if not secrets.compare_digest(header_param, secret.value):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail=(
                "Wrong secret key. If not set through environment variable"
                " 'RD_SYNCRR_SECURITY_SECRET', it was generated automatically at"
                " startup and appears in the server logs."
            ),
        )

    else:
        return True
