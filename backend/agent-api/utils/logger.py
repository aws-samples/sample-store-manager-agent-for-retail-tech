from aws_lambda_powertools import Logger
from config import config


def get_logger(service: str = None) -> Logger:
    log_level = config.LOG_LEVEL
    logger = Logger(service=service or "store-agent-api", level=log_level)
    return logger
