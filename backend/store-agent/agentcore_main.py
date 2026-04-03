import os
import logging
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from agent_router import route_agent_request
from config import config
from payload_validator import PayloadValidationError

log_level = config.LOG_LEVEL
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload, context):
    try:
        logger.info(
            f"Processing request for session: {payload.get('session_id', 'unknown')}"
        )

        result = route_agent_request(payload)

        return result

    except PayloadValidationError as e:
        logger.error(f"Payload validation error: {str(e)}")
        return {"error": f"必須パラメータが不足しています: {str(e)}"}
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {"error": f"処理中にエラーが発生しました: {str(e)}"}


if __name__ == "__main__":
    app.run()
