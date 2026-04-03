"""
Pytest configuration and shared fixtures for API tests
"""

import pytest
import requests
import boto3
import time
import uuid
import os
import jwt
from datetime import datetime, timedelta


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def generate_test_jwt_token():
    """Generate a test JWT token for local testing"""
    payload = {
        "sub": "LOCAL_API_TEST_user",
        "cognito:username": "LOCAL_API_TEST_user",
        "cognito:groups": ["LOCAL_API_TEST_store"],
        "email": "test@example.com",
        "iss": "https://cognito-idp.ap-northeast-1.amazonaws.com/test",
        "aud": "test-client-id",
        "token_use": "id",
        "auth_time": int(datetime.utcnow().timestamp()),
        "iat": int(datetime.utcnow().timestamp()),
        "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
    }
    token = jwt.encode(payload, "secret", algorithm="HS256")
    return token


def get_auth_headers():
    """Get authentication headers from environment variable"""
    auth_header = os.getenv("COGNITO_AUTH_HEADER")
    if auth_header:
        return {"Authorization": auth_header}
    
    test_token = generate_test_jwt_token()
    return {"Authorization": f"Bearer {test_token}"}


def load_config():
    """Load configuration from environment variables"""
    import os

    return {
        "s3_tables": {
            "table_bucket_arn": os.getenv("TABLE_BUCKET_ARN", ""),
            "namespace": os.getenv("NAMESPACE", "store_data"),
        },
        "athena": {
            "workgroup": os.getenv("ATHENA_WORKGROUP", "primary"),
            "output_location": os.getenv("ATHENA_OUTPUT_LOCATION", ""),
        },
    }


def execute_athena_delete(table_name: str, record_ids: list):
    """Execute physical DELETE query via Athena"""
    if not record_ids:
        return

    import os

    config = load_config()
    region = os.getenv("REGION", "ap-northeast-1")
    athena_client = boto3.client("athena", region_name=region)

    s3_tables_config = config.get("s3_tables", {})
    table_bucket_arn = s3_tables_config.get("table_bucket_arn")
    namespace = s3_tables_config.get("namespace", "store_data")
    table_bucket_name = table_bucket_arn.split("/")[-1]
    catalog_name = f"s3tablescatalog/{table_bucket_name}"

    athena_config = config.get("athena", {})
    workgroup = athena_config.get("workgroup", "primary")
    output_location = athena_config.get("output_location")

    placeholders = ", ".join(["?" for _ in record_ids])
    
    if table_name == "daily_survey_answers":
        query = f"""
        DELETE FROM "{catalog_name}"."{namespace}"."{table_name}"
        WHERE survey_id IN ({placeholders})
        """
    else:
        query = f"""
        DELETE FROM "{catalog_name}"."{namespace}"."{table_name}"
        WHERE id IN ({placeholders})
        """

    response = athena_client.start_query_execution(
        QueryString=query,
        WorkGroup=workgroup,
        ResultConfiguration={"OutputLocation": output_location},
        ExecutionParameters=record_ids,
    )

    execution_id = response["QueryExecutionId"]

    while True:
        status_response = athena_client.get_query_execution(
            QueryExecutionId=execution_id
        )
        status = status_response["QueryExecution"]["Status"]["State"]

        if status == "SUCCEEDED":
            break
        elif status in ["FAILED", "CANCELLED"]:
            raise Exception(f"Delete query failed: {status}")

        time.sleep(2)


@pytest.fixture
def api_client():
    """HTTP client for API requests (assumes Docker services running)"""

    class APIClient:
        def __init__(self, base_url):
            self.base_url = base_url
            self.default_headers = get_auth_headers()

        def get(self, path, **kwargs):
            headers = kwargs.pop("headers", {})
            headers.update(self.default_headers)
            return requests.get(f"{self.base_url}{path}", headers=headers, **kwargs)

        def post(self, path, **kwargs):
            headers = kwargs.pop("headers", {})
            headers.update(self.default_headers)
            return requests.post(f"{self.base_url}{path}", headers=headers, **kwargs)

        def put(self, path, **kwargs):
            headers = kwargs.pop("headers", {})
            headers.update(self.default_headers)
            return requests.put(f"{self.base_url}{path}", headers=headers, **kwargs)

        def delete(self, path, **kwargs):
            headers = kwargs.pop("headers", {})
            headers.update(self.default_headers)
            return requests.delete(f"{self.base_url}{path}", headers=headers, **kwargs)

    return APIClient(API_BASE_URL)


@pytest.fixture
def test_data_tracker():
    """作成したテストデータのIDを追跡し、テスト後に物理削除"""
    created_ids = {
        "admin_survey_questions": [],
        "admin_messages": [],
        "daily_survey_summary": [],
        "daily_survey_answers": [],
    }

    yield created_ids

    for table_name, ids in created_ids.items():
        if ids:
            try:
                execute_athena_delete(table_name, ids)
                print(f"Cleaned up {len(ids)} records from {table_name}")
            except Exception as e:
                print(f"Failed to cleanup {table_name}: {e}")


@pytest.fixture
def sample_question_data():
    return {
        "question_text": "LOCAL_API_TEST 今日の業務はいかがでしたか？",
        "question_type": "rating",
        "is_active": True,
    }


@pytest.fixture
def sample_message_data():
    return {
        "title": "LOCAL_API_TEST テストお知らせ",
        "content": "これはテスト用のお知らせです。",
        "is_active": True,
    }


@pytest.fixture
def sample_survey_data():
    return {
        "survey_id": f"LOCAL_API_TEST_{uuid.uuid4()}",
        "answers": [
            {
                "question_id": "q1",
                "question_text": "LOCAL_API_TEST 今日の業務はいかがでしたか？",
                "question_type": "rating",
                "answer_value": "4",
            }
        ],
    }


@pytest.fixture
def sample_chat_data():
    return {
        "agent_type": "hearing",
        "prompt": "LOCAL_API_TEST こんにちは、今日の調子はいかがですか？",
        "session_id": f"LOCAL_API_TEST_session_{uuid.uuid4()}",
        "survey_id": f"LOCAL_API_TEST_{uuid.uuid4()}",
    }


@pytest.fixture
def sample_insights_params():
    return {
        "report_date": "2024-12-14",
    }
