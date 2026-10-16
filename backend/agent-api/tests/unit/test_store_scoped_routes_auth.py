from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

import jwt
import pytest
from fastapi.testclient import TestClient

import main
import routes.chat
import routes.insights
import routes.survey
from utils.exceptions import NotFoundException

STORE_CD = "store_001"
USER_SUB = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
INSIGHT_ID = "insight-001"
SURVEY_ID = "survey-001"
TIMESTAMP = "2026-10-01T09:00:00"


@dataclass(frozen=True)
class RouteCase:
    name: str
    method: str
    path: str
    params: dict | None
    body: dict | None
    service: Any
    method_name: str
    success_return: Any
    not_found_mode: str
    extract_str_cd: Callable[[Any], str]


def _str_cd_from_current_user(position: int) -> Callable[[Any], str]:
    return lambda call_args: call_args.args[position].str_cd


def _str_cd_from_arg(position: int) -> Callable[[Any], str]:
    return lambda call_args: call_args.args[position]


INSIGHT_RESPONSE = {
    "id": INSIGHT_ID,
    "user_cd": USER_SUB,
    "str_cd": STORE_CD,
    "report_date": TIMESTAMP,
    "status": "completed",
    "report_text": "report",
    "session_id": "session-001",
    "actor_id": USER_SUB,
    "created_at": TIMESTAMP,
    "updated_at": TIMESTAMP,
}

SURVEY_RESPONSE = {
    "survey_id": SURVEY_ID,
    "user_cd": USER_SUB,
    "str_cd": STORE_CD,
    "answers": [],
    "created_at": TIMESTAMP,
    "updated_at": TIMESTAMP,
}

CHAT_SESSION_RESPONSE = {
    "session_id": "session-001",
    "survey_id": SURVEY_ID,
    "user_cd": USER_SUB,
    "str_cd": STORE_CD,
    "messages": [],
    "created_at": TIMESTAMP,
}

ROUTE_CASES = [
    RouteCase(
        name="put_insight",
        method="PUT",
        path=f"/api/insights/daily/{INSIGHT_ID}",
        params=None,
        body={
            "report_date": TIMESTAMP,
            "status": "completed",
            "report_text": "report",
            "session_id": "session-001",
        },
        service=routes.insights.insights_service,
        method_name="save_daily_insights",
        success_return={"id": INSIGHT_ID},
        not_found_mode="raise",
        extract_str_cd=_str_cd_from_current_user(0),
    ),
    RouteCase(
        name="put_insight_feedback",
        method="PUT",
        path=f"/api/insights/daily/{INSIGHT_ID}/feedback",
        params=None,
        body={"user_feedback": "good"},
        service=routes.insights.insights_service,
        method_name="save_feedback",
        success_return={"id": INSIGHT_ID},
        not_found_mode="raise",
        extract_str_cd=_str_cd_from_arg(2),
    ),
    RouteCase(
        name="get_insight",
        method="GET",
        path=f"/api/insights/daily/{INSIGHT_ID}",
        params=None,
        body=None,
        service=routes.insights.insights_service,
        method_name="get_insight_by_id",
        success_return=INSIGHT_RESPONSE,
        not_found_mode="raise",
        extract_str_cd=_str_cd_from_arg(1),
    ),
    RouteCase(
        name="put_survey_answer",
        method="PUT",
        path=f"/api/survey/answers/{SURVEY_ID}",
        params=None,
        body={"answers": []},
        service=routes.survey.survey_service,
        method_name="update_survey_answer",
        success_return={"message": "updated", "survey_id": SURVEY_ID},
        not_found_mode="raise",
        extract_str_cd=_str_cd_from_current_user(2),
    ),
    RouteCase(
        name="get_survey_answer",
        method="GET",
        path=f"/api/survey/answers/{SURVEY_ID}",
        params=None,
        body=None,
        service=routes.survey.survey_service,
        method_name="get_survey_answer",
        success_return=SURVEY_RESPONSE,
        not_found_mode="raise",
        extract_str_cd=_str_cd_from_current_user(1),
    ),
    RouteCase(
        name="get_chat_session",
        method="GET",
        path="/api/chat/session",
        params={"survey_id": SURVEY_ID},
        body=None,
        service=routes.chat.chat_service,
        method_name="get_chat_session_by_survey",
        success_return=CHAT_SESSION_RESPONSE,
        not_found_mode="none",
        extract_str_cd=_str_cd_from_current_user(1),
    ),
]


@pytest.fixture
def client():
    return TestClient(main.app)


@pytest.fixture
def bearer_token():
    now = datetime.now(timezone.utc)
    payload = {
        "sub": USER_SUB,
        "cognito:username": "test_user",
        "cognito:groups": [STORE_CD],
        "email": "test@example.com",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
    }
    return jwt.encode(payload, "secret", algorithm="HS256")


def _send(client: TestClient, case: RouteCase, headers: dict):
    return client.request(
        case.method,
        case.path,
        params=case.params,
        json=case.body,
        headers=headers,
    )


@pytest.mark.parametrize("case", ROUTE_CASES, ids=lambda c: c.name)
def test_missing_authorization_header_is_rejected(client, mocker, case):
    service_mock = mocker.patch.object(case.service, case.method_name)

    response = _send(client, case, headers={})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    service_mock.assert_not_called()


@pytest.mark.parametrize("case", ROUTE_CASES, ids=lambda c: c.name)
def test_non_bearer_authorization_header_is_rejected(client, mocker, case):
    service_mock = mocker.patch.object(case.service, case.method_name)

    response = _send(client, case, headers={"Authorization": "Token xxx"})

    assert response.status_code == 401
    service_mock.assert_not_called()


@pytest.mark.parametrize("case", ROUTE_CASES, ids=lambda c: c.name)
def test_valid_bearer_token_passes_store_scope_to_service(
    client, mocker, bearer_token, case
):
    service_mock = mocker.patch.object(
        case.service, case.method_name, return_value=case.success_return
    )

    response = _send(
        client, case, headers={"Authorization": f"Bearer {bearer_token}"}
    )

    assert response.status_code == 200
    service_mock.assert_called_once()
    assert case.extract_str_cd(service_mock.call_args) == STORE_CD


@pytest.mark.parametrize("case", ROUTE_CASES, ids=lambda c: c.name)
def test_resource_outside_store_scope_returns_not_found(
    client, mocker, bearer_token, case
):
    if case.not_found_mode == "raise":
        service_mock = mocker.patch.object(
            case.service,
            case.method_name,
            side_effect=NotFoundException("Resource", "unknown-id"),
        )
    else:
        service_mock = mocker.patch.object(
            case.service, case.method_name, return_value=None
        )

    response = _send(
        client, case, headers={"Authorization": f"Bearer {bearer_token}"}
    )

    assert response.status_code == 404
    service_mock.assert_called_once()
