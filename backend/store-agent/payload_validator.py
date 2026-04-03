import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class PayloadValidationError(Exception):
    """Payloadバリデーションエラー"""

    pass


def validate_agent_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    エージェント実行用のpayloadを検証

    Args:
        payload: 検証対象のpayload

    Returns:
        検証済みのパラメータ辞書

    Raises:
        PayloadValidationError: 必須パラメータが不足している場合
    """
    required_params = ["agent_type", "prompt", "session_id", "actor_id", "str_cd"]
    missing_params = [
        p for p in required_params if p not in payload or payload[p] is None
    ]

    if missing_params:
        error_msg = f"Required parameters are missing: {', '.join(missing_params)}"
        logger.error(error_msg)
        raise PayloadValidationError(error_msg)

    return {
        "agent_type": payload["agent_type"],
        "prompt": payload["prompt"],
        "session_id": payload["session_id"],
        "actor_id": payload["actor_id"],
        "str_cd": payload["str_cd"],
    }
