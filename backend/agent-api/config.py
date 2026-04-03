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
        self.NAMESPACE = os.environ["NAMESPACE"]
        self.ATHENA_WORKGROUP = os.environ["ATHENA_WORKGROUP"]
        self.AGENTCORE_RUNTIME_ARN = os.environ["AGENTCORE_RUNTIME_ARN"]
        self.AGENTCORE_REGION = os.environ["AGENTCORE_REGION"]
        self.HEARING_AGENTCORE_MEMORY_ID = os.environ["HEARING_AGENTCORE_MEMORY_ID"]
        self.DAILY_SUMMARY_AGENTCORE_MEMORY_ID = os.environ[
            "DAILY_SUMMARY_AGENTCORE_MEMORY_ID"
        ]

        self.REGION = os.getenv("REGION", "ap-northeast-1")
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

        logger.info("Configuration loaded successfully")

    def _validate_required_env(self):
        """必須環境変数の検証"""
        required_vars = [
            "TABLE_BUCKET_ARN",
            "ATHENA_OUTPUT_LOCATION",
            "NAMESPACE",
            "ATHENA_WORKGROUP",
            "AGENTCORE_RUNTIME_ARN",
            "AGENTCORE_REGION",
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
