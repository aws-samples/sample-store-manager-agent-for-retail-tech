import time
from typing import Dict, Any, List, Optional

import boto3
from pyathena import connect
from pyathena.error import OperationalError, ProgrammingError
from config import config
from utils.logger import get_logger

logger = get_logger("database")


class DatabaseException(Exception):
    """データベース操作エラー"""

    pass


def get_athena_client():
    """Athenaクライアントを取得"""
    region = config.REGION
    return boto3.client("athena", region_name=region)


def get_catalog_info() -> Dict[str, str]:
    table_bucket_arn = config.TABLE_BUCKET_ARN
    bucket_name = table_bucket_arn.split("/")[-1] if table_bucket_arn else ""
    catalog_name = f"s3tablescatalog/{bucket_name}"
    database_name = config.NAMESPACE

    return {
        "bucket_name": bucket_name,
        "catalog_name": catalog_name,
        "database_name": database_name,
    }


def execute_athena_query(
    query: str, execution_parameters: Optional[List[str]] = None
) -> Optional[str]:
    try:
        athena_client = get_athena_client()
        output_location = config.ATHENA_OUTPUT_LOCATION

        logger.info("Executing Athena query...")
        logger.debug(f"Query: {query}")

        query_params = {
            "QueryString": query,
            "ResultConfiguration": {"OutputLocation": output_location},
        }

        if execution_parameters:
            query_params["ExecutionParameters"] = execution_parameters

        response = athena_client.start_query_execution(**query_params)

        execution_id = response["QueryExecutionId"]
        logger.info(f"Query execution started: {execution_id}")
        return execution_id

    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise DatabaseException(f"Failed to execute query: {str(e)}")


def wait_for_query_completion(execution_id: str, max_wait_seconds: int = 300) -> bool:
    try:
        athena_client = get_athena_client()
        logger.info(f"Waiting for query completion: {execution_id}")

        start_time = time.time()
        while True:
            if time.time() - start_time > max_wait_seconds:
                logger.error(f"Query timeout after {max_wait_seconds} seconds")
                raise DatabaseException(
                    f"Query timeout after {max_wait_seconds} seconds"
                )

            response = athena_client.get_query_execution(QueryExecutionId=execution_id)

            status = response["QueryExecution"]["Status"]["State"]

            if status == "SUCCEEDED":
                logger.info("Query completed successfully")
                return True
            elif status in ["FAILED", "CANCELLED"]:
                error_reason = response["QueryExecution"]["Status"].get(
                    "StateChangeReason", "Unknown error"
                )
                logger.error(f"Query failed: {error_reason}")
                raise DatabaseException(f"Query failed: {error_reason}")

            time.sleep(1)

    except DatabaseException:
        raise
    except Exception as e:
        logger.error(f"Error waiting for query completion: {e}")
        raise DatabaseException(f"Failed to wait for query completion: {str(e)}")


def get_query_results(execution_id: str) -> List[Dict[str, Any]]:
    try:
        athena_client = get_athena_client()
        logger.info("Retrieving query results...")

        results = []
        next_token = None
        columns = []

        while True:
            if next_token:
                response = athena_client.get_query_results(
                    QueryExecutionId=execution_id, NextToken=next_token
                )
            else:
                response = athena_client.get_query_results(
                    QueryExecutionId=execution_id
                )

            if not columns:
                column_info = response["ResultSet"]["ResultSetMetadata"]["ColumnInfo"]
                columns = [col["Name"] for col in column_info]

            rows = response["ResultSet"]["Rows"]
            if not results:
                rows = rows[1:]

            for row in rows:
                row_data = {}
                for i, data in enumerate(row["Data"]):
                    value = data.get("VarCharValue")
                    row_data[columns[i]] = value
                results.append(row_data)

            next_token = response.get("NextToken")
            if not next_token:
                break

        logger.info(f"Retrieved {len(results)} rows")
        return results

    except Exception as e:
        logger.error(f"Error retrieving query results: {e}")
        raise DatabaseException(f"Failed to retrieve query results: {str(e)}")


def get_pyathena_connection():
    return connect(
        s3_staging_dir=config.ATHENA_OUTPUT_LOCATION,
        region_name=config.REGION,
    )


def execute_query_with_pyathena(
    query: str, parameters: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    try:
        conn = get_pyathena_connection()
        cursor = conn.cursor()
        cursor.execute(query, parameters)

        if cursor.description is None:
            return []

        columns = [desc[0] for desc in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        return results
    except (OperationalError, ProgrammingError) as e:
        logger.error(f"PyAthena query error: {e}")
        raise DatabaseException(f"Failed to execute query: {str(e)}")
    except Exception as e:
        logger.error(f"Error executing query with PyAthena: {e}")
        raise DatabaseException(f"Failed to execute query: {str(e)}")


def execute_query_and_get_results(
    query: str, execution_parameters: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    execution_id = execute_athena_query(query, execution_parameters)
    if not execution_id:
        raise DatabaseException("Failed to execute query")

    wait_for_query_completion(execution_id)
    return get_query_results(execution_id)
