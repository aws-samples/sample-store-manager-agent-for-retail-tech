import json
import boto3
import uuid
from pathlib import Path


def load_config():
    cdk_outputs_path = (
        Path(__file__).parent.parent.parent.parent / "cdk" / ".cdk-outputs.json"
    )
    with open(cdk_outputs_path) as f:
        outputs = json.load(f)

    backend_stack = outputs["BackendStack"]
    return {
        "runtime_arn": backend_stack["AgentCoreRuntimeArn"],
        "region": backend_stack["AgentCoreRuntimeArn"].split(":")[3],
        "hearing_memory_id": backend_stack["HearingMemoryId"],
        "daily_summary_memory_id": backend_stack["DailySummaryMemoryId"],
    }


def test_agent_invoke():
    config = load_config()
    client = boto3.client("bedrock-agentcore", region_name=config["region"])

    session_id = str(uuid.uuid4())

    test_payload = {
        "agent_type": "daily_summary",
        "prompt": "前日のsurveyデータと売上データを取得してレポートをまとめて",
        "session_id": session_id,
        "actor_id": "test_user_001",
        "str_cd": "test_store_001",
    }

    print(f"Invoking: {json.dumps(test_payload, ensure_ascii=False)}")

    response = client.invoke_agent_runtime(
        agentRuntimeArn=config["runtime_arn"],
        payload=json.dumps(test_payload),
        qualifier="DEFAULT",
    )

    response_body = response["response"].read()
    result = json.loads(response_body)

    print(f"\nResponse: {json.dumps(result, ensure_ascii=False, indent=2)}")
    return result


def test_hearing_agent():
    config = load_config()
    client = boto3.client("bedrock-agentcore", region_name=config["region"])

    session_id = str(uuid.uuid4())

    test_payload = {
        "agent_type": "hearing",
        "prompt": "今日の店舗状況についてヒアリングして",
        "session_id": session_id,
        "actor_id": "test_user_001",
        "str_cd": "test_store_001",
    }

    print(f"Invoking: {json.dumps(test_payload, ensure_ascii=False)}")

    response = client.invoke_agent_runtime(
        agentRuntimeArn=config["runtime_arn"],
        payload=json.dumps(test_payload),
        qualifier="DEFAULT",
    )

    response_body = response["response"].read()
    result = json.loads(response_body)

    print(f"\nResponse: {json.dumps(result, ensure_ascii=False, indent=2)}")

    test_payload = {
        "agent_type": "hearing",
        "prompt": "レジが大変だった",
        "session_id": session_id,
        "actor_id": "test_user_001",
        "str_cd": "test_store_001",
    }

    print(f"Invoking: {json.dumps(test_payload, ensure_ascii=False)}")

    response = client.invoke_agent_runtime(
        agentRuntimeArn=config["runtime_arn"],
        payload=json.dumps(test_payload),
        qualifier="DEFAULT",
    )

    response_body = response["response"].read()
    result = json.loads(response_body)

    print(f"\nResponse: {json.dumps(result, ensure_ascii=False, indent=2)}")

    return result


if __name__ == "__main__":
    print("=== AgentCore Runtime Test ===\n")

    print("Test 1: Daily Summary Agent")
    test_agent_invoke()

    print("\n" + "=" * 50 + "\n")

    print("Test 2: Hearing Agent")
    test_hearing_agent()
