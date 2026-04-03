"""
Shared Bedrock model configuration
"""

import boto3
from strands.models import BedrockModel
import os
from config import config

BEDROCK_MODEL_ID = config.BEDROCK_MODEL_ID
BEDROCK_REGION = config.BEDROCK_REGION
BEDROCK_TEMPERATURE = 0.0


def get_bedrock_model() -> BedrockModel:
    """
    Create and return a configured BedrockModel instance.

    Returns:
        BedrockModel: Configured Bedrock model instance
    """
    return BedrockModel(
        model_id=BEDROCK_MODEL_ID,
        temperature=BEDROCK_TEMPERATURE,
        streaming=False,
        boto_session=boto3.Session(region_name=BEDROCK_REGION),
    )


# Export the model instance for direct import
bedrock_model = get_bedrock_model()
