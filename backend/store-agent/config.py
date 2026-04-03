import os
import logging

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """設定エラー"""

    pass


class Config:
    """環境変数の一括管理クラス"""

    def __init__(self):
        self._validate_required_env()

        self.TABLE_BUCKET_ARN = os.environ["TABLE_BUCKET_ARN"]
        self.ATHENA_OUTPUT_LOCATION = os.environ["ATHENA_OUTPUT_LOCATION"]
        self.PROMPT_BUCKET_NAME = os.environ["PROMPT_BUCKET_NAME"]
        self.NAMESPACE = os.environ["NAMESPACE"]
        self.PROMPT_PREFIX = os.environ["PROMPT_PREFIX"]
        self.HEARING_AGENTCORE_MEMORY_ID = os.environ["HEARING_AGENTCORE_MEMORY_ID"]
        self.DAILY_SUMMARY_AGENTCORE_MEMORY_ID = os.environ[
            "DAILY_SUMMARY_AGENTCORE_MEMORY_ID"
        ]

        self.REGION = os.getenv("REGION", "ap-northeast-1")
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
        self.BEDROCK_MODEL_ID = os.getenv(
            "BEDROCK_MODEL_ID", "jp.anthropic.claude-haiku-4-5-20251001-v1:0"
        )
        self.BEDROCK_REGION = os.getenv("BEDROCK_REGION", "ap-northeast-1")

        logger.info("Configuration loaded successfully")

    def _validate_required_env(self):
        """必須環境変数の検証"""
        required_vars = [
            "TABLE_BUCKET_ARN",
            "ATHENA_OUTPUT_LOCATION",
            "PROMPT_BUCKET_NAME",
            "NAMESPACE",
            "PROMPT_PREFIX",
            "HEARING_AGENTCORE_MEMORY_ID",
            "DAILY_SUMMARY_AGENTCORE_MEMORY_ID",
        ]

        missing_vars = [var for var in required_vars if not os.environ.get(var)]

        if missing_vars:
            error_msg = (
                f"Required environment variables are missing: {', '.join(missing_vars)}"
            )
            logger.error(error_msg)
            raise ConfigError(error_msg)


config = Config()
