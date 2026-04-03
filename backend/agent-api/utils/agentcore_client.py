import json
import boto3
from botocore.config import Config
from typing import Dict, Any
from bedrock_agentcore.memory import MemoryClient
from config import config
from utils.logger import get_logger

logger = get_logger("agentcore-client")


def get_memory_client(region: str = None) -> MemoryClient:
    region = region or config.AGENTCORE_REGION
    return MemoryClient(region_name=region)


def invoke_agentcore_runtime(
    agent_type: str,
    prompt: str,
    session_id: str,
    actor_id: str,
    str_cd: str,
) -> Dict[str, Any]:
    runtime_arn = config.AGENTCORE_RUNTIME_ARN
    region = config.AGENTCORE_REGION

    boto_config = Config(
        connect_timeout=90,
        read_timeout=90
    )
    client = boto3.client("bedrock-agentcore", region_name=region, config=boto_config)

    payload = {
        "agent_type": agent_type,
        "prompt": prompt,
        "session_id": session_id,
        "actor_id": actor_id,
        "str_cd": str_cd,
    }

    logger.info(
        f"Invoking AgentCore Runtime: agent_type={agent_type}, session_id={session_id}"
    )

    try:
        response = client.invoke_agent_runtime(
            agentRuntimeArn=runtime_arn,
            runtimeSessionId=f"{session_id}_{'0' * 21}",
            payload=json.dumps(payload),
            qualifier="DEFAULT",
        )

        response_body = response["response"].read()
        result = json.loads(response_body)

        logger.info(
            f"AgentCore Runtime raw response: {json.dumps(result, ensure_ascii=False)}"
        )

        if "response" in result:
            logger.info(f"Found 'response' in result")
            response_data = result["response"]
            logger.info(
                f"Response structure: {json.dumps(response_data, ensure_ascii=False)}"
            )

            # response_dataが文字列の場合
            if isinstance(response_data, str):
                logger.info(f"Response is string: {response_data[:100]}...")
                return {
                    "response": response_data,
                    "agent_type": agent_type,
                    "session_id": session_id,
                    "actor_id": actor_id,
                }

            # response_dataが辞書の場合
            content = response_data.get("content", [])
            if content and isinstance(content, list):
                text = content[0].get("text", "")
                logger.info(f"Extracted text: {text[:100]}...")
                return {
                    "response": text,
                    "agent_type": agent_type,
                    "session_id": session_id,
                    "actor_id": actor_id,
                }

        logger.warning(f"Fallback: returning str(result)")
        return {
            "response": str(result),
            "agent_type": agent_type,
            "session_id": session_id,
            "actor_id": actor_id,
        }

    except Exception as e:
        logger.error(f"AgentCore Runtime invocation failed: {e}")
        raise
