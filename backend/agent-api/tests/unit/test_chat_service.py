import pytest
from unittest.mock import MagicMock
from utils.chat_service import ChatService
from utils.exceptions import NotFoundException
from utils.auth import CurrentUser
from routes.schema.chat import ChatSessionSaveRequest, ChatSessionResponse


def _make_current_user() -> CurrentUser:
    return CurrentUser(
        user_cd="test_user",
        actor_id="test_actor",
        str_cd="test_store",
        username="test_user",
        email="test@example.com",
    )


def _session_row() -> dict:
    return {
        "agentcore_memory_id": "test_memory",
        "session_id": "session-123",
        "actor_id": "test_actor",
        "survey_id": "survey-123",
        "user_cd": "test_user",
        "str_cd": "test_store",
        "created_at": "2026-10-16 09:00:00",
        "created_at_jst": "2026-10-16 09:00:00",
    }


@pytest.fixture
def mock_memory_client(mocker):
    memory_client = MagicMock()
    memory_client.get_last_k_turns.return_value = []
    mocker.patch("utils.chat_service.get_memory_client", return_value=memory_client)
    return memory_client


@pytest.fixture
def mock_athena_client(mocker):
    athena_client = MagicMock()
    athena_client.start_query_execution.return_value = {"QueryExecutionId": "x"}
    mocker.patch("utils.chat_service.boto3.client", return_value=athena_client)
    return athena_client


def test_get_chat_session_by_survey_filters_by_store(mocker, mock_memory_client):
    mock_execute = mocker.patch(
        "utils.chat_service._execute_athena_query", return_value=[]
    )

    ChatService().get_chat_session_by_survey("survey-123", _make_current_user())

    query, params = mock_execute.call_args.args
    assert "a.str_cd = ?" in query
    assert params == ["survey-123", "test_store"]


def test_get_chat_session_by_survey_returns_none_when_not_found(
    mocker, mock_memory_client
):
    mocker.patch("utils.chat_service._execute_athena_query", return_value=[])

    result = ChatService().get_chat_session_by_survey(
        "survey-123", _make_current_user()
    )

    assert result is None


def test_get_chat_session_by_survey_returns_session(mocker, mock_memory_client):
    mocker.patch(
        "utils.chat_service._execute_athena_query", return_value=[_session_row()]
    )

    result = ChatService().get_chat_session_by_survey(
        "survey-123", _make_current_user()
    )

    assert isinstance(result, ChatSessionResponse)
    assert result.session_id == "session-123"
    assert result.survey_id == "survey-123"
    assert result.str_cd == "test_store"
    assert result.messages == []


def test_save_chat_session_rejects_survey_of_other_store(mocker, mock_athena_client):
    mock_execute = mocker.patch(
        "utils.chat_service._execute_athena_query", return_value=[{"_col0": "1"}]
    )
    request = ChatSessionSaveRequest(survey_id="survey-123", session_id="session-123")

    with pytest.raises(NotFoundException):
        ChatService().save_chat_session(request, _make_current_user())

    query, params = mock_execute.call_args.args
    assert "str_cd <> ?" in query
    assert params == ["survey-123", "test_store"]
    mock_athena_client.start_query_execution.assert_not_called()


def test_save_chat_session_inserts_when_no_other_store_owner(
    mocker, mock_athena_client
):
    mock_execute = mocker.patch(
        "utils.chat_service._execute_athena_query", return_value=[]
    )
    request = ChatSessionSaveRequest(survey_id="survey-123", session_id="session-123")

    result = ChatService().save_chat_session(request, _make_current_user())

    assert result == {"message": "Chat session saved successfully"}
    _, params = mock_execute.call_args.args
    assert "test_store" in params
    mock_athena_client.start_query_execution.assert_called_once()
    insert_params = mock_athena_client.start_query_execution.call_args.kwargs[
        "ExecutionParameters"
    ]
    assert "survey-123" in insert_params
