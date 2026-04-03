import pytest
import os
from unittest.mock import MagicMock, patch
from utils.database import (
    get_catalog_info,
    execute_athena_query,
    wait_for_query_completion,
    get_query_results,
    execute_query_and_get_results,
    DatabaseException,
)


def test_get_catalog_info():
    result = get_catalog_info()
    
    expected_bucket_arn = os.environ["TABLE_BUCKET_ARN"]
    expected_bucket_name = expected_bucket_arn.split("/")[-1]
    expected_namespace = os.environ["NAMESPACE"]
    
    assert result["bucket_name"] == expected_bucket_name
    assert result["catalog_name"] == f"s3tablescatalog/{expected_bucket_name}"
    assert result["database_name"] == expected_namespace


def test_execute_athena_query_success(mocker):
    mock_client = MagicMock()
    mock_client.start_query_execution.return_value = {"QueryExecutionId": "exec-123"}
    mocker.patch("utils.database.get_athena_client", return_value=mock_client)

    result = execute_athena_query("SELECT * FROM table")

    assert result == "exec-123"
    mock_client.start_query_execution.assert_called_once()


def test_execute_athena_query_with_parameters(mocker):
    mock_client = MagicMock()
    mock_client.start_query_execution.return_value = {"QueryExecutionId": "exec-456"}
    mocker.patch("utils.database.get_athena_client", return_value=mock_client)

    result = execute_athena_query("SELECT * FROM table WHERE id = ?", ["test-id"])

    assert result == "exec-456"
    call_args = mock_client.start_query_execution.call_args[1]
    assert call_args["ExecutionParameters"] == ["test-id"]


def test_execute_athena_query_error(mocker):
    mock_client = MagicMock()
    mock_client.start_query_execution.side_effect = Exception("Query failed")
    mocker.patch("utils.database.get_athena_client", return_value=mock_client)

    with pytest.raises(DatabaseException, match="Failed to execute query"):
        execute_athena_query("SELECT * FROM table")


def test_wait_for_query_completion_success(mocker):
    mock_client = MagicMock()
    mock_client.get_query_execution.return_value = {
        "QueryExecution": {"Status": {"State": "SUCCEEDED"}}
    }
    mocker.patch("utils.database.get_athena_client", return_value=mock_client)

    result = wait_for_query_completion("exec-123")

    assert result is True


def test_wait_for_query_completion_failed(mocker):
    mock_client = MagicMock()
    mock_client.get_query_execution.return_value = {
        "QueryExecution": {
            "Status": {"State": "FAILED", "StateChangeReason": "Syntax error"}
        }
    }
    mocker.patch("utils.database.get_athena_client", return_value=mock_client)

    with pytest.raises(DatabaseException, match="Query failed: Syntax error"):
        wait_for_query_completion("exec-123")


def test_wait_for_query_completion_timeout(mocker):
    mock_client = MagicMock()
    mock_client.get_query_execution.return_value = {
        "QueryExecution": {"Status": {"State": "RUNNING"}}
    }
    mocker.patch("utils.database.get_athena_client", return_value=mock_client)

    with pytest.raises(DatabaseException, match="Query timeout"):
        wait_for_query_completion("exec-123", max_wait_seconds=1)


def test_get_query_results_success(mocker):
    mock_client = MagicMock()
    mock_client.get_query_results.return_value = {
        "ResultSet": {
            "ResultSetMetadata": {"ColumnInfo": [{"Name": "id"}, {"Name": "name"}]},
            "Rows": [
                {"Data": [{"VarCharValue": "id"}, {"VarCharValue": "name"}]},
                {"Data": [{"VarCharValue": "1"}, {"VarCharValue": "test"}]},
            ],
        }
    }
    mocker.patch("utils.database.get_athena_client", return_value=mock_client)

    result = get_query_results("exec-123")

    assert len(result) == 1
    assert result[0]["id"] == "1"
    assert result[0]["name"] == "test"


def test_get_query_results_empty(mocker):
    mock_client = MagicMock()
    mock_client.get_query_results.return_value = {
        "ResultSet": {
            "ResultSetMetadata": {"ColumnInfo": [{"Name": "id"}]},
            "Rows": [{"Data": [{"VarCharValue": "id"}]}],
        }
    }
    mocker.patch("utils.database.get_athena_client", return_value=mock_client)

    result = get_query_results("exec-123")

    assert len(result) == 0


def test_get_query_results_error(mocker):
    mock_client = MagicMock()
    mock_client.get_query_results.side_effect = Exception("Failed to get results")
    mocker.patch("utils.database.get_athena_client", return_value=mock_client)

    with pytest.raises(DatabaseException, match="Failed to retrieve query results"):
        get_query_results("exec-123")


def test_execute_query_and_get_results_success(mocker):
    mocker.patch("utils.database.execute_athena_query", return_value="exec-123")
    mocker.patch("utils.database.wait_for_query_completion", return_value=True)
    mocker.patch("utils.database.get_query_results", return_value=[{"id": "1"}])

    result = execute_query_and_get_results("SELECT * FROM table")

    assert len(result) == 1
    assert result[0]["id"] == "1"


def test_execute_query_and_get_results_no_execution_id(mocker):
    mocker.patch("utils.database.execute_athena_query", return_value=None)

    with pytest.raises(DatabaseException, match="Failed to execute query"):
        execute_query_and_get_results("SELECT * FROM table")
