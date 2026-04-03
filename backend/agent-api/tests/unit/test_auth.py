import pytest
from fastapi import HTTPException
from utils.auth import get_current_user, CurrentUser
import jwt
from datetime import datetime, timedelta, timezone


def test_get_current_user_success():
    payload = {
        "sub": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "cognito:username": "test_user",
        "cognito:groups": ["test_store", "test_group_b"],
        "email": "test@example.com",
        "iss": "https://cognito-idp.us-west-2.amazonaws.com/us-west-2_example",
        "aud": "xxxxxxxxxxxxexample",
        "token_use": "id",
        "auth_time": int(datetime.now(timezone.utc).timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
    }
    token = jwt.encode(payload, "secret", algorithm="HS256")
    authorization = f"Bearer {token}"
    
    user = get_current_user(authorization)
    
    assert user.user_cd == "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    assert user.actor_id == "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    assert user.str_cd == "test_store"
    assert user.username == "test_user"
    assert user.email == "test@example.com"


def test_get_current_user_invalid_header_no_bearer():
    with pytest.raises(HTTPException) as exc_info:
        get_current_user("InvalidToken")
    
    assert exc_info.value.status_code == 401
    assert "Invalid authorization header" in exc_info.value.detail


def test_get_current_user_invalid_header_empty():
    with pytest.raises(HTTPException) as exc_info:
        get_current_user("")
    
    assert exc_info.value.status_code == 401
    assert "Invalid authorization header" in exc_info.value.detail


def test_get_current_user_missing_sub():
    payload = {
        "cognito:username": "test_user",
        "cognito:groups": ["test_store"],
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
    }
    token = jwt.encode(payload, "secret", algorithm="HS256")
    authorization = f"Bearer {token}"
    
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(authorization)
    
    assert exc_info.value.status_code == 401
    assert "Missing sub claim" in exc_info.value.detail


def test_get_current_user_missing_username():
    payload = {
        "sub": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "cognito:groups": ["test_store"],
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
    }
    token = jwt.encode(payload, "secret", algorithm="HS256")
    authorization = f"Bearer {token}"
    
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(authorization)
    
    assert exc_info.value.status_code == 401
    assert "Missing cognito:username claim" in exc_info.value.detail


def test_get_current_user_missing_groups():
    payload = {
        "sub": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "cognito:username": "test_user",
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
    }
    token = jwt.encode(payload, "secret", algorithm="HS256")
    authorization = f"Bearer {token}"
    
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(authorization)
    
    assert exc_info.value.status_code == 403
    assert "User has no groups" in exc_info.value.detail


def test_get_current_user_empty_groups():
    payload = {
        "sub": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "cognito:username": "test_user",
        "cognito:groups": [],
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
    }
    token = jwt.encode(payload, "secret", algorithm="HS256")
    authorization = f"Bearer {token}"
    
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(authorization)
    
    assert exc_info.value.status_code == 403
    assert "User has no groups" in exc_info.value.detail


def test_get_current_user_invalid_token():
    authorization = "Bearer invalid.token.format"
    
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(authorization)
    
    assert exc_info.value.status_code == 401
    assert "Invalid token" in exc_info.value.detail


def test_get_current_user_multiple_groups():
    payload = {
        "sub": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "cognito:username": "test_user",
        "cognito:groups": ["store_001", "store_002", "admin_group"],
        "email": "test@example.com",
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
    }
    token = jwt.encode(payload, "secret", algorithm="HS256")
    authorization = f"Bearer {token}"
    
    user = get_current_user(authorization)
    
    assert user.str_cd == "store_001"


def test_get_current_user_without_email():
    payload = {
        "sub": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "cognito:username": "test_user",
        "cognito:groups": ["test_store"],
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
    }
    token = jwt.encode(payload, "secret", algorithm="HS256")
    authorization = f"Bearer {token}"
    
    user = get_current_user(authorization)
    
    assert user.email is None
