"""
S3 Transfer Script
Uploads CSV files from test-data directory to S3 bucket
"""

import json
import os
from pathlib import Path
from typing import Dict

import boto3
from botocore.exceptions import ClientError


def load_config(config_path: str = "config.json") -> Dict:
    """Load configuration from JSON file"""
    with open(config_path, "r") as f:
        return json.load(f)


def ensure_bucket_exists(s3_client, bucket_name: str) -> bool:
    """
    Check if S3 bucket exists, create if it doesn't

    Args:
        s3_client: boto3 S3 client
        bucket_name: Name of the S3 bucket

    Returns:
        bool: True if bucket exists or was created successfully
    """
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"Bucket '{bucket_name}' already exists")
        return True
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "404":
            # Bucket doesn't exist, create it
            try:
                # Get the region from the client
                region = s3_client.meta.region_name

                if region and region != "us-east-1":
                    # For regions other than us-east-1, specify LocationConstraint
                    s3_client.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration={"LocationConstraint": region},
                    )
                else:
                    # For us-east-1, don't specify LocationConstraint
                    s3_client.create_bucket(Bucket=bucket_name)

                print(
                    f"Bucket '{bucket_name}' created successfully in region '{region}'"
                )
                return True
            except ClientError as create_error:
                print(f"Error creating bucket: {create_error}")
                return False
        else:
            print(f"Error checking bucket: {e}")
            return False


def get_data_mapping():
    """Get data mapping configuration for file uploads."""
    return [
        # Sales data files
        {
            "table_name": "m_item",
            "schema": "schema/sales-data/m_item.csv",
            "data": "test-data/sales-data/m_item.csv",
        },
        {
            "table_name": "t_daily_store_traffic",
            "schema": "schema/sales-data/t_daily_store_traffic.csv",
            "data": "test-data/sales-data/t_daily_store_traffic.csv",
        },
        {
            "table_name": "t_sales",
            "schema": "schema/sales-data/t_sales.csv",
            "data": "test-data/sales-data/t_sales.csv",
        },
        {
            "table_name": "t_str_daily_budget",
            "schema": "schema/sales-data/t_str_daily_budget.csv",
            "data": "test-data/sales-data/t_str_daily_budget.csv",
        },
        # Survey data files
        {
            "table_name": "ai_chat_history",
            "schema": "schema/survey/ai_chat_history.csv",
            "data": "test-data/survey/ai_chat_history.csv",
        },
        {
            "table_name": "daily_survey_answers",
            "schema": "schema/survey/daily_survey_answers.csv",
            "data": "test-data/survey/daily_survey_answers.csv",
        },
        {
            "table_name": "daily_survey_summary",
            "schema": "schema/survey/daily_survey_summary.csv",
            "data": "test-data/survey/daily_survey_summary.csv",
        },
        # Admin data files
        {
            "table_name": "admin_messages",
            "schema": "schema/admin/admin_messages.csv",
            "data": "test-data/admin/admin_messages.csv",
        },
        {
            "table_name": "admin_survey",
            "schema": "schema/admin/admin_survey.csv",
            "data": "test-data/admin/admin_survey.csv",
        },
    ]


def upload_csv_files_from_mapping(
    bucket_name: str, prefix: str = ""
) -> tuple[int, int]:
    """
    Upload CSV files based on data mapping configuration

    Args:
        bucket_name: Name of the S3 bucket
        prefix: S3 key prefix (folder path)

    Returns:
        tuple: (uploaded_count, failed_count)
    """
    s3_client = boto3.client("s3")

    # Ensure bucket exists
    if not ensure_bucket_exists(s3_client, bucket_name):
        print("Failed to ensure bucket exists. Aborting upload.")
        return 0, 0

    # Get data mapping
    data_mappings = get_data_mapping()

    print(f"\nFound {len(data_mappings)} file(s) to upload based on mapping")

    # Upload each file
    uploaded_count = 0
    failed_count = 0

    for mapping in data_mappings:
        table_name = mapping["table_name"]
        data_path = mapping["data"]

        # Check if data file exists
        if not Path(data_path).exists():
            print(f"✗ Data file not found: {data_path}")
            failed_count += 1
            continue

        try:
            # Determine S3 data type from data path
            data_type = "unknown"
            if "sales-data" in data_path:
                data_type = "sales-data"
            elif "admin" in data_path:
                data_type = "admin"
            elif "survey" in data_path:
                data_type = "daily-survey"  # Map to S3 structure

            # Create S3 key: prefix + data_type + table_name + filename
            filename = Path(data_path).name
            s3_key = (
                f"{prefix}{data_type}/{table_name}/{filename}"
                if prefix
                else f"{data_type}/{table_name}/{filename}"
            )

            # Upload file
            s3_client.upload_file(data_path, bucket_name, s3_key)

            print(f"✓ Uploaded: {data_path} -> s3://{bucket_name}/{s3_key}")
            uploaded_count += 1

        except ClientError as e:
            print(f"✗ Failed to upload {data_path}: {e}")
            failed_count += 1

    # Summary
    print(f"\n  Upload Summary:")
    print(f"    Total files: {len(data_mappings)}")
    print(f"    Uploaded: {uploaded_count}")
    print(f"    Failed: {failed_count}")

    return uploaded_count, failed_count


def main():
    """Main execution function"""
    # Load configuration
    config = load_config()
    s3_config = config.get("s3", {})

    bucket_name = s3_config.get("bucket_name")
    base_prefix = s3_config.get("prefix", "")

    if not bucket_name:
        print("Error: bucket_name not specified in config.json")
        return

    print(f"S3 Transfer Configuration:")
    print(f"  Bucket: {bucket_name}")
    print(f"  Base Prefix: {base_prefix}")
    print(f"{'=' * 60}")

    # Upload files based on mapping configuration
    print(f"\nProcessing files based on data mapping configuration...")

    uploaded, failed = upload_csv_files_from_mapping(
        bucket_name=bucket_name, prefix=base_prefix
    )

    print(f"\n{'=' * 60}")
    print(f"Final Summary:")
    print(f"  Total uploaded: {uploaded}")
    print(f"  Total failed: {failed}")
    print(f"All uploads completed!")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
