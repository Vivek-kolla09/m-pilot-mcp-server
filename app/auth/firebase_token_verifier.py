
import logging

import httpx
from mcp.server.auth.provider import AccessToken

from app.services.backend_client import BackendClient

logger = logging.getLogger(__name__)


class FirebaseTokenVerifier:
    """Validates Firebase ID tokens through the M-Pilot backend."""

    def __init__(self):
        self.backend = BackendClient()

    async def verify_token(self, token: str) -> AccessToken | None:
        """
        Validate a Firebase ID token using the backend's
        Firebase Admin SDK authentication endpoint.
        """

        try:
            result = await self.backend.get(
                endpoint="/api/v1/auth/me",
                firebase_id_token=token,
            )

            user = result.get("user", {})
            firebase_uid = user.get("firebase_uid")

            if not firebase_uid:
                logger.warning(
                    "Authentication response did not contain a Firebase UID."
                )
                return None

            email = user.get("email")

            return AccessToken(
                token=token,
                client_id="firebase",
                scopes=[],
                subject=firebase_uid,
                claims={"email": email} if email else {},
            )

        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Firebase authentication rejected by backend: HTTP %s",
                exc.response.status_code,
            )
            return None

        except httpx.RequestError:
            logger.exception(
                "Unable to reach the M-Pilot backend for authentication."
            )
            return None

        except (KeyError, AttributeError, TypeError):
            logger.exception(
                "Unexpected authentication response from the backend."
            )
            return None


# Understanding the implementation
# Component	            |Responsibility
# FirebaseTokenVerifier	|Implements MCP's token verification interface
# BackendClient	        |Sends the token to FastAPI
# /api/v1/auth/me	    |Validates the token using Firebase Admin SDK
# firebase_uid	        |Supplies the verified user's identity
# AccessToken	        |Gives MCP the authenticated identity

# Important security decisions:
# - Invalid or expired tokens are rejected.
# - Backend connectivity failures fail closed.
# - The token is never printed or logged.
# - The verifier does not trust a user ID supplied by an MCP client.
# - Firebase Admin SDK remains responsible for token and revocation validation.
# The token is retained in the SDK's AccessToken object because the verifier must return it, but we won't expose it to the LLM or include it in tool responses.

