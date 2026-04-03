from fastapi import HTTPException, status, Header
from typing import Optional
from pydantic import BaseModel
import jwt


class CurrentUser(BaseModel):
    user_cd: str
    actor_id: str
    str_cd: str
    username: str
    email: Optional[str]


def get_current_user(authorization: str = Header(...)) -> CurrentUser:
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing sub claim"
        )
    
    username = payload.get("cognito:username")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing cognito:username claim"
        )
    
    groups = payload.get("cognito:groups", [])
    if not groups:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no groups"
        )
    
    return CurrentUser(
        user_cd=sub,
        actor_id=sub,
        str_cd=groups[0],
        username=username,
        email=payload.get("email")
    )
