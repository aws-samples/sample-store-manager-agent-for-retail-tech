import boto3
import os
from config import config


class PromptLoader:
    def __init__(self):
        self.s3_client = boto3.client("s3")
        self.bucket_name = config.PROMPT_BUCKET_NAME
        self.prefix = config.PROMPT_PREFIX

    def load_prompt(self, filename: str) -> str:
        key = f"{self.prefix}{filename}"

        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            return response["Body"].read().decode("utf-8")
        except Exception as e:
            raise RuntimeError(f"Failed to load prompt from S3: {key}") from e
