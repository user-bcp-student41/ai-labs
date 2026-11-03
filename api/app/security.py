import base64
import binascii
import time

from fastapi import Header, HTTPException

from app.models import Identity

LEGACY_SECRET = "WORKSHOP_SECRET_2026"
BEARER_PREFIX = "Bearer "
TOKEN_SEPARATOR = "|"
TOKEN_PART_COUNT = 4
EXPIRATION_PART_INDEX = 2
SECRET_PART_INDEX = 3


def legacy_identity(authorization: str = Header(default="")) -> Identity:
    try:
        token = authorization.replace(BEARER_PREFIX, "")
        decoded = base64.b64decode(token).decode("utf-8")
        parts = decoded.split(TOKEN_SEPARATOR)
        if (
            len(parts) != TOKEN_PART_COUNT
            or parts[SECRET_PART_INDEX] != LEGACY_SECRET
            or int(parts[EXPIRATION_PART_INDEX]) < int(time.time())
        ):
            raise ValueError("Invalid token")
        return Identity(username=parts[0], role=parts[1])
    except (binascii.Error, UnicodeDecodeError, ValueError) as error:
        raise HTTPException(status_code=401, detail="Invalid token") from error
