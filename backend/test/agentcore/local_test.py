#!/usr/bin/env python3
"""
Store Agent Main Entry Point
"""

import logging
import sys
from pathlib import Path
import json
import os
import uuid

cdk_outputs_path = (
    Path(__file__).parent.parent.parent.parent / "cdk" / ".cdk-outputs.json"
)
with open(cdk_outputs_path, "r") as f:
    cdk_outputs = json.load(f).get("BackendStack", {})

table_bucket_arn = cdk_outputs.get("TableBucketArn", "")
region = table_bucket_arn.split(":")[3] if table_bucket_arn else "ap-northeast-1"

os.environ["REGION"] = region
os.environ["PROMPT_BUCKET_NAME"] = cdk_outputs.get("PromptBucketName", "")
os.environ["PROMPT_PREFIX"] = "prompt/"
os.environ["HEARING_AGENTCORE_MEMORY_ID"] = cdk_outputs.get("HearingMemoryId", "")
os.environ["DAILY_SUMMARY_AGENTCORE_MEMORY_ID"] = cdk_outputs.get(
    "DailySummaryMemoryId", ""
)
os.environ["TABLE_BUCKET_ARN"] = table_bucket_arn
os.environ["NAMESPACE"] = cdk_outputs.get("NamespaceName", "")
os.environ["ATHENA_OUTPUT_LOCATION"] = cdk_outputs.get("AthenaOutputLocation", "")

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "store-agent"))
from agent_router import route_agent_request

log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def run_agent():
    logger.info("=== Run Strands Agent===")
    session_id = str(uuid.uuid4())
    queries = [
        {
            "agent_type": "daily_summary",
            "prompt": "まず前日のsurveyデータ、売上データをtoolで取得し、その後レポートをまとめて",
            "session_id": f"summary_test_{session_id}",
            "actor_id": "test_user_001",
            "str_cd": "test_store_001",
        },
        {
            "agent_type": "hearing",
            "prompt": "今日の店舗状況についてヒアリングして",
            "session_id": f"hearing_test_{session_id}",
            "actor_id": "test_user_001",
            "str_cd": "test_store_001",
        },
        {
            "agent_type": "hearing",
            "prompt": "レジが大変だった",
            "session_id": f"hearing_test_{session_id}",
            "actor_id": "hearing_store_staff1",
            "str_cd": "test_store_001",
        },
    ]

    for i, query in enumerate(queries, 1):
        logger.info(f"\n--- Example {i} ---")
        logger.info(f"Agent Type: {query['agent_type']}")
        logger.info(f"Query: {query['prompt']}")

        try:
            response = route_agent_request(query)
            logger.info(f"Response: {response}")

        except Exception as e:
            logger.error(f"Error: {str(e)}")

    logger.info("\n=== Example Complete ===")


if __name__ == "__main__":
    run_agent()
