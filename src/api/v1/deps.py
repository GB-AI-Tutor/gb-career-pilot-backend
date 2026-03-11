from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from src.database.database import get_supabase_client
from src.utils.security import decode_jwt_token

# We changed from HTTPOthpasswordbaeare to HTTPBearer because it is flexible in swager UI then previous one.

# This automatically extract the token from the request
http_bearer = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(http_bearer)):
    token = credentials.credentials

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # FIX: Ensure algorithms is a list [settings.ALGORITHM]
        payload = decode_jwt_token(token)
        # Token payload is {"user_data": {"sub": "...", "email": "..."}, "exp": ...}
        user_data = payload.get("user_data", {})
        user_id: str = user_data.get("sub")
        if user_id is None:
            raise credentials_exception

    except JWTError as e:
        raise credentials_exception from e

    client = get_supabase_client()

    # Using .single() is good, but let's handle the potential error
    try:
        response = client.table("users").select("*").eq("id", user_id).single().execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="User not found")
        return response.data
    except Exception as e:
        raise credentials_exception from e
