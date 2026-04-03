import logging
from typing import Dict, Any
from daily_summary_agent import create_daily_summary_agent
from hearing_agent import create_hearing_agent
from payload_validator import validate_agent_payload, PayloadValidationError

logger = logging.getLogger(__name__)


def route_agent_request(payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        validated = validate_agent_payload(payload)

        agent_type = validated["agent_type"]
        user_message = validated["prompt"]
        session_id = validated["session_id"]
        actor_id = validated["actor_id"]
        str_cd = validated["str_cd"]

        logger.info(f"Routing to agent_type: {agent_type}, session: {session_id}")

        if agent_type == "hearing":
            agent = create_hearing_agent(session_id=session_id, actor_id=actor_id)
            if not user_message:
                user_message = "今日の店舗状況はいかがでしたか？"
        else:
            agent = create_daily_summary_agent(
                session_id=session_id, actor_id=actor_id, str_cd=str_cd
            )
            if not user_message:
                user_message = "前日のsurveyデータ、売上データをtoolで取得し、その後レポートをまとめて"

        result = agent(user_message)

        return {
            "response": result.message,
            "agent_type": agent_type,
            "session_id": session_id,
            "actor_id": actor_id,
        }

    except PayloadValidationError as e:
        logger.error(f"Payload validation error: {str(e)}")
        return {"error": f"必須パラメータが不足しています: {str(e)}"}
    except Exception as e:
        logger.error(f"Error in agent routing: {str(e)}")
        return {"error": f"エージェント処理中にエラーが発生しました: {str(e)}"}
