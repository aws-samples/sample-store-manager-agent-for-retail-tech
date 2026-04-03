import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_database(mocker):
    mock_execute = mocker.patch("utils.database.execute_query_and_get_results")
    mock_catalog = mocker.patch("utils.database.get_catalog_info")

    mock_catalog.return_value = {
        "bucket_name": "test-bucket",
        "catalog_name": "s3tablescatalog/test-bucket",
        "database_name": "test_database",
    }

    return {"execute_query": mock_execute, "catalog_info": mock_catalog}


@pytest.fixture
def mock_agentcore_runtime(mocker):
    mock_invoke = mocker.patch("utils.agentcore_client.invoke_agentcore_runtime")

    mock_invoke.return_value = {
        "response": "モックレスポンステキスト",
        "agent_type": "hearing",
        "session_id": "test-session-id",
        "actor_id": "test-actor-id",
    }

    return mock_invoke


@pytest.fixture
def mock_memory_client(mocker):
    mock_client = mocker.MagicMock()
    mocker.patch("utils.agentcore_client.get_memory_client", return_value=mock_client)

    return mock_client


@pytest.fixture
def mock_boto3_clients(mocker):
    mock_athena = mocker.MagicMock()
    mock_bedrock = mocker.MagicMock()

    def client_factory(service_name, **kwargs):
        if service_name == "athena":
            return mock_athena
        elif service_name == "bedrock-agentcore":
            return mock_bedrock
        return mocker.MagicMock()

    mocker.patch("boto3.client", side_effect=client_factory)

    return {"athena": mock_athena, "bedrock_agentcore": mock_bedrock}
