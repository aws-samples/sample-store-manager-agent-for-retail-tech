#!/usr/bin/env python3
"""
Delete all tables script for cleaning up Glue Catalog CSV tables and S3 Tables.
This script removes both temporary CSV tables from Glue Catalog and Iceberg tables from S3 Tables.
"""

import json
import boto3
import logging
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TableCleaner:
    """Deletes all tables from both Glue Catalog and S3 Tables."""

    def __init__(self, config_path: str = "config.json"):
        """Initialize with configuration."""
        self.config = self._load_config(config_path)
        self.s3tables_client = boto3.client("s3tables")
        self.athena_client = boto3.client("athena")
        self.glue_client = boto3.client("glue")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            sys.exit(1)

    def _get_table_bucket_info(self) -> Dict[str, str]:
        """Get Table Bucket information from config."""
        s3_tables_config = self.config.get("s3_tables", {})
        table_bucket_arn = s3_tables_config.get("table_bucket_arn")

        if not table_bucket_arn:
            raise ValueError(
                "table_bucket_arn not found in config.json s3_tables section"
            )

        return {"table_bucket_arn": table_bucket_arn}

    def _get_namespace_info(self) -> Dict[str, str]:
        """Get Namespace information from config."""
        s3_tables_config = self.config.get("s3_tables", {})
        namespace = s3_tables_config.get("namespace")
        table_bucket_arn = s3_tables_config.get("table_bucket_arn")

        if not namespace:
            raise ValueError("namespace not found in config.json s3_tables section")
        if not table_bucket_arn:
            raise ValueError(
                "table_bucket_arn not found in config.json s3_tables section"
            )

        table_bucket_name = table_bucket_arn.split("/")[-1]

        return {"namespace": namespace, "table_bucket_name": table_bucket_name}

    def _get_table_mapping(self) -> List[Dict[str, str]]:
        """Get table mapping configuration matching create_s3_tables.py."""
        return [
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
            {
                "table_name": "ai_chat_history",
                "schema": "schema/survey/ai_chat_history.csv",
                "data": "test-data/daily-report/ai_chat_history.csv",
            },
            {
                "table_name": "daily_survey_answers",
                "schema": "schema/survey/daily_survey_answers.csv",
                "data": "test-data/daily-report/daily_survey_answers.csv",
            },
            {
                "table_name": "daily_survey_summary",
                "schema": "schema/survey/daily_survey_summary.csv",
                "data": "test-data/daily-report/daily_survey_summary.csv",
            },
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

    def _get_temp_database_name(self) -> str:
        """Get temporary database name from config."""
        temp_config = self.config.get("temp_catalog", {})
        database_name = temp_config.get("database_name", "temp_csv_catalog")
        return database_name

    def _get_table_names(self) -> List[str]:
        """Get list of table names to delete."""
        table_mappings = self._get_table_mapping()
        return [mapping["table_name"] for mapping in table_mappings]

    def _wait_for_query_completion(
        self, query_execution_id: str, timeout: int = 300
    ) -> bool:
        """Wait for Athena query completion."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                response = self.athena_client.get_query_execution(
                    QueryExecutionId=query_execution_id
                )

                status = response["QueryExecution"]["Status"]["State"]

                if status == "SUCCEEDED":
                    logger.info(f"Query {query_execution_id} completed successfully")
                    return True
                elif status in ["FAILED", "CANCELLED"]:
                    reason = response["QueryExecution"]["Status"].get(
                        "StateChangeReason", "Unknown error"
                    )
                    logger.warning(f"Query {query_execution_id} failed: {reason}")
                    return False

                time.sleep(2)

            except Exception as e:
                logger.error(f"Error checking query status: {e}")
                return False

        logger.error(f"Query {query_execution_id} timed out after {timeout} seconds")
        return False

    def delete_glue_catalog_tables(self) -> bool:
        """Delete all CSV tables from Glue Catalog."""
        logger.info("Starting Glue Catalog table deletion")

        table_names = self._get_table_names()
        temp_database_name = self._get_temp_database_name()
        success_count = 0

        for table_name in table_names:
            temp_table_name = f"temp_{table_name}_csv"

            try:
                logger.info(
                    f"Deleting Glue Catalog table: {temp_database_name}.{temp_table_name}"
                )

                self.glue_client.delete_table(
                    DatabaseName=temp_database_name, Name=temp_table_name
                )

                success_count += 1
                logger.info(
                    f"✅ Successfully deleted Glue Catalog table: {temp_table_name}"
                )

            except self.glue_client.exceptions.EntityNotFoundException:
                logger.info(
                    f"ℹ️  Glue Catalog table not found (already deleted): {temp_table_name}"
                )
            except Exception as e:
                logger.error(
                    f"❌ Error deleting Glue Catalog table {temp_table_name}: {e}"
                )

        try:
            response = self.glue_client.get_tables(DatabaseName=temp_database_name)
            remaining_tables = response.get("TableList", [])

            if not remaining_tables:
                logger.info(f"Deleting empty temporary database: {temp_database_name}")
                self.glue_client.delete_database(Name=temp_database_name)
                logger.info(
                    f"✅ Successfully deleted temporary database: {temp_database_name}"
                )
            else:
                logger.info(
                    f"Keeping temporary database {temp_database_name} - {len(remaining_tables)} tables remain"
                )

        except self.glue_client.exceptions.EntityNotFoundException:
            logger.info(
                f"ℹ️  Temporary database not found (already deleted): {temp_database_name}"
            )
        except Exception as e:
            logger.error(f"Error managing temporary database {temp_database_name}: {e}")

        logger.info(
            f"Glue Catalog table deletion completed: {success_count}/{len(table_names)} tables deleted"
        )
        return success_count > 0

    def delete_s3_tables(self) -> bool:
        """Delete all Iceberg tables from S3 Tables."""
        logger.info("Starting S3 Tables deletion")

        try:
            table_bucket_info = self._get_table_bucket_info()
            namespace_info = self._get_namespace_info()
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            return False

        table_names = self._get_table_names()
        success_count = 0

        for table_name in table_names:
            try:
                logger.info(f"Deleting S3 Table: {table_name}")

                self.s3tables_client.delete_table(
                    tableBucketARN=table_bucket_info["table_bucket_arn"],
                    namespace=namespace_info["namespace"],
                    name=table_name,
                )

                success_count += 1
                logger.info(f"✅ Successfully deleted S3 Table: {table_name}")

            except self.s3tables_client.exceptions.NotFoundException:
                logger.info(f"ℹ️  S3 Table not found (already deleted): {table_name}")
            except Exception as e:
                logger.error(f"❌ Error deleting S3 Table {table_name}: {e}")

        logger.info(
            f"S3 Tables deletion completed: {success_count}/{len(table_names)} tables deleted"
        )
        return success_count > 0

    def delete_all_tables(self) -> bool:
        """Delete all tables from both catalogs."""
        logger.info("Starting complete table cleanup process")

        glue_success = self.delete_glue_catalog_tables()
        s3_success = self.delete_s3_tables()

        overall_success = glue_success or s3_success

        if overall_success:
            logger.info("✅ Table cleanup completed successfully")
        else:
            logger.warning("⚠️  Table cleanup completed with some failures")

        return overall_success

    def list_remaining_tables(self) -> None:
        """List any remaining tables in both catalogs."""
        logger.info("Checking for remaining tables...")

        # Check Glue Catalog
        try:
            temp_database_name = self._get_temp_database_name()

            try:
                response = self.glue_client.get_tables(DatabaseName=temp_database_name)
                glue_tables = [table["Name"] for table in response.get("TableList", [])]
                temp_tables = [
                    name
                    for name in glue_tables
                    if name.startswith("temp_") and name.endswith("_csv")
                ]

                if temp_tables:
                    logger.warning(
                        f"Remaining Glue Catalog tables in {temp_database_name}: {temp_tables}"
                    )
                else:
                    logger.info(
                        f"✅ No remaining temporary tables in Glue Catalog database: {temp_database_name}"
                    )

            except self.glue_client.exceptions.EntityNotFoundException:
                logger.info(
                    f"✅ Temporary database {temp_database_name} not found (already deleted)"
                )

        except Exception as e:
            logger.error(f"Error checking Glue Catalog tables: {e}")

        # Check S3 Tables
        try:
            table_bucket_info = self._get_table_bucket_info()
            namespace_info = self._get_namespace_info()

            response = self.s3tables_client.list_tables(
                tableBucketARN=table_bucket_info["table_bucket_arn"],
                namespace=namespace_info["namespace"],
            )

            s3_tables = [table["name"] for table in response.get("tables", [])]

            if s3_tables:
                logger.warning(f"Remaining S3 Tables: {s3_tables}")
            else:
                logger.info("✅ No remaining tables in S3 Tables")

        except Exception as e:
            logger.error(f"Error checking S3 Tables: {e}")


def main():
    """Main execution function."""
    try:
        cleaner = TableCleaner()

        success = cleaner.delete_all_tables()

        print("\n" + "=" * 60)
        cleaner.list_remaining_tables()
        print("=" * 60)

        if success:
            print(f"\n✅ Table cleanup process completed!")
        else:
            print(f"\n❌ Table cleanup process failed!")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
