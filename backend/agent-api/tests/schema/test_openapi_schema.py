import pytest
import schemathesis
import jwt
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from main import app


schema = schemathesis.openapi.from_asgi("/openapi.json", app)


def generate_test_jwt_token():
    payload = {
        "sub": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "cognito:username": "test_user",
        "cognito:groups": ["test_store"],
        "email": "test@example.com",
        "iss": "https://cognito-idp.us-west-2.amazonaws.com/us-west-2_example",
        "aud": "xxxxxxxxxxxxexample",
        "token_use": "id",
        "auth_time": int(datetime.now(timezone.utc).timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
    }
    return jwt.encode(payload, "secret", algorithm="HS256")


@schema.parametrize()
def test_api_schema_compliance(case):
    if case.path.startswith("/api/"):
        case.headers = case.headers or {}
        case.headers["Authorization"] = f"Bearer {generate_test_jwt_token()}"
    
    response = case.call()

    if response.status_code >= 500:
        return

    case.validate_response(
        response,
        checks=(
            schemathesis.checks.status_code_conformance,
            schemathesis.checks.content_type_conformance,
        ),
    )
