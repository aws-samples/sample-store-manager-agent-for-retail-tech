import pytest
from unittest.mock import MagicMock


@pytest.fixture(autouse=True, scope="function")
def mock_all_external_dependencies_for_schema_tests(monkeypatch):
    mock_athena = MagicMock()
    mock_athena.start_query_execution.return_value = {
        "QueryExecutionId": "test-exec-id"
    }
    mock_athena.get_query_execution.return_value = {
        "QueryExecution": {"Status": {"State": "SUCCEEDED"}}
    }
    mock_athena.get_query_results.return_value = {
        "ResultSet": {
            "ResultSetMetadata": {"ColumnInfo": [{"Name": "id"}]},
            "Rows": [{"Data": [{"VarCharValue": "id"}]}],
        }
    }

    mock_bedrock = MagicMock()

    def mock_boto3_client(service_name, **kwargs):
        if service_name == "athena":
            return mock_athena
        elif service_name == "bedrock-agentcore":
            return mock_bedrock
        return MagicMock()

    monkeypatch.setattr("boto3.client", mock_boto3_client)

    mock_agentcore_response = {
        "response": "モックレスポンス",
        "agent_type": "hearing",
        "session_id": "test-session",
        "actor_id": "test-actor",
    }
    monkeypatch.setattr(
        "utils.agentcore_client.invoke_agentcore_runtime",
        lambda *args, **kwargs: mock_agentcore_response,
    )
