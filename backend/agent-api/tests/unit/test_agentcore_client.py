import pytest
import json
from unittest.mock import MagicMock
from utils.agentcore_client import get_memory_client, invoke_agentcore_runtime


def test_get_memory_client_default_region(mocker):
    mock_client_class = mocker.patch("utils.agentcore_client.MemoryClient")

    get_memory_client()

    mock_client_class.assert_called_once_with(region_name="ap-northeast-1")


def test_get_memory_client_custom_region(mocker):
    mock_client_class = mocker.patch("utils.agentcore_client.MemoryClient")

    get_memory_client(region="us-east-1")

    mock_client_class.assert_called_once_with(region_name="us-east-1")


def test_invoke_agentcore_runtime_success(mocker):
    mock_client = MagicMock()
    mock_response_body = MagicMock()
    mock_response_body.read.return_value = json.dumps(
        {"response": {"content": [{"text": "テストレスポンス"}]}}
    ).encode()

    mock_client.invoke_agent_runtime.return_value = {"response": mock_response_body}

    mocker.patch("boto3.client", return_value=mock_client)

    result = invoke_agentcore_runtime(
        agent_type="hearing",
        prompt="テストプロンプト",
        session_id="session-123",
        actor_id="actor-123",
        str_cd="S001",
    )

    assert result["response"] == "テストレスポンス"
    assert result["agent_type"] == "hearing"
    assert result["session_id"] == "session-123"
    assert result["actor_id"] == "actor-123"


def test_invoke_agentcore_runtime_with_kwargs(mocker):
    mock_client = MagicMock()
    mock_response_body = MagicMock()
    mock_response_body.read.return_value = json.dumps(
        {"response": {"content": [{"text": "レスポンス"}]}}
    ).encode()

    mock_client.invoke_agent_runtime.return_value = {"response": mock_response_body}

    mocker.patch("boto3.client", return_value=mock_client)

    result = invoke_agentcore_runtime(
        agent_type="daily_summary",
        prompt="プロンプト",
        session_id="session-456",
        actor_id="actor-456",
        str_cd="S001",
    )

    assert result["response"] == "レスポンス"
    call_args = mock_client.invoke_agent_runtime.call_args[1]
    payload = json.loads(call_args["payload"])
    assert payload["str_cd"] == "S001"


def test_invoke_agentcore_runtime_response_string(mocker):
    mock_client = MagicMock()
    mock_response_body = MagicMock()
    mock_response_body.read.return_value = json.dumps(
        {"response": "シンプルな文字列レスポンス"}
    ).encode()

    mock_client.invoke_agent_runtime.return_value = {"response": mock_response_body}

    mocker.patch("boto3.client", return_value=mock_client)

    result = invoke_agentcore_runtime(
        agent_type="hearing",
        prompt="プロンプト",
        session_id="session-123",
        actor_id="actor-123",
        str_cd="S001",
    )

    assert "response" in result


def test_invoke_agentcore_runtime_error(mocker):
    mock_client = MagicMock()
    mock_client.invoke_agent_runtime.side_effect = Exception("Runtime error")

    mocker.patch("boto3.client", return_value=mock_client)

    with pytest.raises(Exception, match="Runtime error"):
        invoke_agentcore_runtime(
            agent_type="hearing",
            prompt="プロンプト",
            session_id="session-123",
            actor_id="actor-123",
            str_cd="S001",
        )
