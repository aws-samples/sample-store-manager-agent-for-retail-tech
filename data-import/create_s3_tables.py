#!/usr/bin/env python3
"""
AWS S3 Tables catalog creation script for Iceberg tables.
This script creates S3 Tables based on CSV schema definitions and migrates data using CTAS queries.
"""

import json
import csv
import boto3
import logging
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class S3TablesCatalogCreator:
    """Creates AWS S3 Tables catalog from CSV schema definitions."""

    def __init__(self, config_path: str = "config.json"):
        """Initialize with configuration."""
        self.config = self._load_config(config_path)
        self.s3tables_client = boto3.client("s3tables")
        self.athena_client = boto3.client("athena")
        self.s3_client = boto3.client("s3")
        self.glue_client = boto3.client("glue")

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

        # Extract bucket name from ARN: arn:aws:s3tables:region:account:bucket/bucket-name
        table_bucket_name = table_bucket_arn.split("/")[-1]

        return {"namespace": namespace, "table_bucket_name": table_bucket_name}

    def _get_temp_database_name(self) -> str:
        """Get temporary database name from config."""
        temp_config = self.config.get("temp_catalog", {})
        database_name = temp_config.get("database_name", "temp_csv_catalog")
        return database_name

    def _create_temp_database(self, database_name: str) -> bool:
        """Create temporary database for CSV tables if it doesn't exist."""
        try:
            try:
                self.glue_client.get_database(Name=database_name)
                logger.info(f"Temporary database '{database_name}' already exists")
                return True
            except self.glue_client.exceptions.EntityNotFoundException:
                pass

            self.glue_client.create_database(
                DatabaseInput={
                    "Name": database_name,
                    "Description": f"Temporary database for CSV tables during S3 Tables migration",
                }
            )
            logger.info(f"Created temporary database: {database_name}")
            return True

        except Exception as e:
            logger.error(f"Error creating temporary database {database_name}: {e}")
            return False

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

    def _get_table_mapping(self) -> List[Dict[str, str]]:
        """Get table mapping configuration with schema and test-data paths."""
        return [
            # Sales data tables
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
            # Survey data tables
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

    def _read_csv_schema_from_local(
        self, schema_path: str
    ) -> Optional[List[Dict[str, str]]]:
        """Read CSV schema definition from specified schema file path."""
        if not os.path.exists(schema_path):
            logger.warning(f"Schema file not found: {schema_path}")
            return None

        try:
            schema = []
            with open(
                schema_path, "r", encoding="utf-8-sig"
            ) as f:  # utf-8-sig to handle BOM
                reader = csv.DictReader(f)

                # Clean headers to remove any BOM or extra whitespace
                if reader.fieldnames:
                    cleaned_fieldnames = [
                        field.strip().lstrip("\ufeff") for field in reader.fieldnames
                    ]
                    reader.fieldnames = cleaned_fieldnames

                logger.debug(f"CSV headers: {reader.fieldnames}")

                row_count = 0
                for row in reader:
                    row_count += 1

                    # Clean row keys to handle BOM and whitespace
                    cleaned_row = {}
                    for key, value in row.items():
                        clean_key = key.strip().lstrip("\ufeff") if key else key
                        cleaned_row[clean_key] = value

                    logger.debug(f"Row {row_count}: {cleaned_row}")

                    # Skip empty rows or rows without required fields
                    if not cleaned_row.get("column_name") or not cleaned_row.get(
                        "data_type"
                    ):
                        logger.debug(
                            f"Skipping row {row_count}: missing column_name or data_type"
                        )
                        continue

                    # Clean up the data (remove extra whitespace)
                    column_name = cleaned_row["column_name"].strip()
                    data_type = cleaned_row["data_type"].strip()

                    if column_name and data_type:
                        # Safely handle None values for optional fields
                        description = cleaned_row.get("description") or ""
                        constraints = cleaned_row.get("constraints") or ""

                        schema.append(
                            {
                                "column_name": column_name,
                                "data_type": data_type,
                                "description": description.strip()
                                if description
                                else "",
                                "constraints": constraints.strip()
                                if constraints
                                else "",
                            }
                        )
                        logger.debug(f"Added column: {column_name} ({data_type})")

                logger.info(
                    f"Processed {row_count} rows, loaded schema for {schema_path}: {len(schema)} columns"
                )

            return schema if schema else None

        except Exception as e:
            logger.error(f"Error reading schema file {schema_path}: {e}")
            return None

    def _map_data_type_to_iceberg(self, data_type: str) -> str:
        """Map CSV schema data types to Iceberg-compatible types."""
        type_mapping = {
            "string": "string",
            "int": "long",
            "integer": "long",
            "float": "double",
            "double": "double",
            "date": "date",
            "timestamp": "timestamp",
            "boolean": "boolean",
            "bool": "boolean",
        }

        mapped_type = type_mapping.get(data_type.lower(), "string")
        if mapped_type != data_type.lower():
            logger.debug(f"Mapped data type: {data_type} -> {mapped_type}")

        return mapped_type

    def _map_data_type_to_athena(self, data_type: str) -> str:
        """Map CSV schema data types to Athena-compatible types."""
        type_mapping = {
            "string": "string",
            "int": "bigint",
            "integer": "bigint",
            "float": "double",
            "double": "double",
            "date": "date",
            "timestamp": "timestamp",
            "boolean": "boolean",
            "bool": "boolean",
        }

        mapped_type = type_mapping.get(data_type.lower(), "string")
        if mapped_type != data_type.lower():
            logger.debug(f"Mapped data type for Athena: {data_type} -> {mapped_type}")

        return mapped_type

    def _create_s3_table(
        self,
        table_bucket_arn: str,
        namespace: str,
        table_name: str,
        schema: List[Dict[str, str]],
    ) -> bool:
        """Create S3 Table with the given schema."""
        try:
            fields = []

            for col in schema:
                iceberg_data_type = self._map_data_type_to_iceberg(col["data_type"])

                field_def = {
                    "name": col["column_name"],
                    "type": iceberg_data_type,
                    "required": False,
                }
                fields.append(field_def)

            try:
                self.s3tables_client.get_table(
                    tableBucketARN=table_bucket_arn,
                    namespace=namespace,
                    name=table_name,
                )
                logger.info(f"Table '{table_name}' already exists in S3 Tables")
                return True

            except self.s3tables_client.exceptions.NotFoundException:
                self.s3tables_client.create_table(
                    tableBucketARN=table_bucket_arn,
                    namespace=namespace,
                    name=table_name,
                    format="ICEBERG",
                    metadata={"iceberg": {"schema": {"fields": fields}}},
                )
                logger.info(f"Created S3 Table: {table_name}")

            return True

        except Exception as e:
            logger.error(f"Error creating S3 Table {table_name}: {e}")
            return False

    def _generate_temp_table_name(self, table_name: str) -> str:
        """Generate consistent temporary table name."""
        return f"temp_{table_name}_csv"

    def _verify_table_exists(self, table_name: str) -> bool:
        """Verify that Glue Catalog table exists and is accessible."""
        try:
            athena_config = self.config.get("athena", {})
            workgroup = athena_config.get("workgroup", "primary")
            output_location = athena_config.get("output_location")

            temp_database_name = self._get_temp_database_name()
            count_query = f'SELECT COUNT(*) FROM "AwsDataCatalog"."{temp_database_name}"."{table_name}" LIMIT 1'
            logger.info(
                f"Verifying Glue Catalog table accessibility: {temp_database_name}.{table_name}"
            )

            response = self.athena_client.start_query_execution(
                QueryString=count_query,
                WorkGroup=workgroup,
                ResultConfiguration={"OutputLocation": output_location},
            )

            query_id = response["QueryExecutionId"]

            if self._wait_for_query_completion(query_id):
                logger.info(f"Table verified and accessible: {table_name}")
                return True
            else:
                logger.warning(f"Table not accessible: {table_name}")
                return False

        except Exception as e:
            logger.error(f"Error verifying table accessibility for {table_name}: {e}")
            return False

    def _create_temporary_table(
        self, temp_table_name: str, schema: List[Dict[str, str]], s3_location: str
    ) -> str:
        """Create temporary external table using Glue client and return query execution ID."""
        temp_database_name = self._get_temp_database_name()

        if not self._create_temp_database(temp_database_name):
            raise Exception(
                f"Failed to create temporary database: {temp_database_name}"
            )

        columns = []
        for col in schema:
            athena_data_type = self._map_data_type_to_athena(col["data_type"])
            columns.append({"Name": col["column_name"], "Type": athena_data_type})

        try:
            self.glue_client.create_table(
                DatabaseName=temp_database_name,
                TableInput={
                    "Name": temp_table_name,
                    "StorageDescriptor": {
                        "Columns": columns,
                        "Location": s3_location,
                        "InputFormat": "org.apache.hadoop.mapred.TextInputFormat",
                        "OutputFormat": "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
                        "SerdeInfo": {
                            "SerializationLibrary": "org.apache.hadoop.hive.serde2.OpenCSVSerde",
                            "Parameters": {
                                "separatorChar": ",",
                                "skip.header.line.count": "1",
                            },
                        },
                        "StoredAsSubDirectories": False,
                    },
                    "TableType": "EXTERNAL_TABLE",
                },
            )
            logger.info(
                f"Created temporary external table using Glue: {temp_database_name}.{temp_table_name}"
            )
            logger.info(f"S3 location: {s3_location}")

            return "glue-table-created"

        except self.glue_client.exceptions.AlreadyExistsException:
            logger.info(
                f"Temporary table already exists: {temp_database_name}.{temp_table_name}"
            )
            return "glue-table-exists"
        except Exception as e:
            logger.error(f"Error creating temporary table with Glue: {e}")
            raise

    def _execute_ctas(
        self, table_name: str, temp_table_name: str, column_list_str: str
    ) -> str:
        """Execute CTAS query and return query execution ID."""
        namespace_info = self._get_namespace_info()
        temp_database_name = self._get_temp_database_name()

        s3_tables_catalog = f"s3tablescatalog/{namespace_info['table_bucket_name']}"
        s3_tables_database = namespace_info["namespace"]

        ctas_query = f"""
        CREATE TABLE "{s3_tables_catalog}"."{s3_tables_database}"."{table_name}"
        WITH (
            table_type = 'ICEBERG',
            is_external = false
        )
        AS SELECT {column_list_str}
        FROM "AwsDataCatalog"."{temp_database_name}"."{temp_table_name}"
        """

        athena_config = self.config.get("athena", {})
        workgroup = athena_config.get("workgroup", "primary")
        output_location = athena_config.get("output_location")

        logger.info(f"Executing CTAS query for: {table_name}")

        logger.info(f"Executing query:\n{ctas_query}")

        response = self.athena_client.start_query_execution(
            QueryString=ctas_query,
            WorkGroup=workgroup,
            ResultConfiguration={"OutputLocation": output_location},
        )

        return response["QueryExecutionId"]

    def _cleanup_temporary_table(self, temp_table_name: str) -> bool:
        """Clean up temporary table using Glue client."""
        try:
            temp_database_name = self._get_temp_database_name()

            self.glue_client.delete_table(
                DatabaseName=temp_database_name, Name=temp_table_name
            )
            logger.info(
                f"Cleaned up temporary table using Glue: {temp_database_name}.{temp_table_name}"
            )
            return True

        except self.glue_client.exceptions.EntityNotFoundException:
            logger.info(
                f"Temporary table not found (already deleted): {temp_table_name}"
            )
            return True
        except Exception as e:
            logger.error(f"Error cleaning up temporary table {temp_table_name}: {e}")
            return False

    def _execute_ctas_query(
        self, table_name: str, data_type: str, schema: List[Dict[str, str]]
    ) -> bool:
        """Execute CTAS query to migrate data from CSV to S3 Tables."""
        try:
            bucket_name = self.config["s3"]["bucket_name"]
            prefix = self.config["s3"]["prefix"]
            s3_location = f"s3://{bucket_name}/{prefix}{data_type}/{table_name}/"

            column_list = []
            for col in schema:
                column_list.append(f'"{col["column_name"]}"')
            column_list_str = ", ".join(column_list)

            temp_table_name = self._generate_temp_table_name(table_name)

            athena_config = self.config.get("athena", {})
            output_location = athena_config.get("output_location")

            if not output_location:
                raise ValueError("athena.output_location not found in config.json")

            logger.info(f"Starting CTAS process for table: {table_name}")
            logger.info(f"Temporary table name: {temp_table_name}")

            temp_query_id = self._create_temporary_table(
                temp_table_name, schema, s3_location
            )

            if temp_query_id in ["glue-table-created", "glue-table-exists"]:
                logger.info(f"Temporary table ready: {temp_table_name}")
            else:
                logger.error(f"Failed to create temporary table: {temp_table_name}")
                return False

            logger.info("Verifying temporary table existence...")
            if not self._verify_table_exists(temp_table_name):
                logger.error(f"Temporary table does not exist: {temp_table_name}")
                return False

            ctas_query_id = self._execute_ctas(
                table_name, temp_table_name, column_list_str
            )

            logger.info(f"Waiting for CTAS completion (Query ID: {ctas_query_id})")
            success = self._wait_for_query_completion(ctas_query_id)

            if success:
                logger.info(
                    "CTAS completed successfully, cleaning up temporary table..."
                )
                self._cleanup_temporary_table(temp_table_name)
            else:
                logger.error(f"CTAS failed for table: {table_name}")

            return success

        except Exception as e:
            logger.error(f"Error executing CTAS query for {table_name}: {e}")
            return False

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
                    logger.error(f"Query {query_execution_id} failed: {reason}")
                    return False

                time.sleep(5)

            except Exception as e:
                logger.error(f"Error checking query status: {e}")
                return False

        logger.error(f"Query {query_execution_id} timed out after {timeout} seconds")
        return False

    def create_s3_tables_catalog(self) -> bool:
        """Create complete S3 Tables catalog."""
        logger.info("Starting S3 Tables catalog creation process")

        try:
            table_bucket_info = self._get_table_bucket_info()
            namespace_info = self._get_namespace_info()
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            return False

        table_mappings = self._get_table_mapping()
        if not table_mappings:
            logger.warning("No table mappings found")
            return False

        success_count = 0
        total_count = len(table_mappings)

        for mapping in table_mappings:
            table_name = mapping["table_name"]
            schema_path = mapping["schema"]
            data_path = mapping["data"]

            logger.info(f"Processing table: {table_name}")
            logger.info(f"  Schema: {schema_path}")
            logger.info(f"  Data: {data_path}")

            schema = self._read_csv_schema_from_local(schema_path)
            if not schema:
                logger.warning(
                    f"Skipping {table_name} - no schema found or schema file is empty"
                )
                continue

            logger.info(f"Found schema for {table_name}: {len(schema)} columns")

            data_type = "unknown"
            if "sales-data" in data_path:
                data_type = "sales-data"
            elif "survey" in data_path:
                data_type = "daily-survey"
            elif "admin" in data_path:
                data_type = "admin"

            if self._execute_ctas_query(table_name, data_type, schema):
                success_count += 1
                logger.info(f"✅ Successfully processed table: {table_name}")
            else:
                logger.error(f"❌ Failed to migrate data for table: {table_name}")

        logger.info(
            f"S3 Tables catalog creation completed: {success_count}/{total_count} tables created successfully"
        )
        return success_count > 0

    def list_catalog_info(self) -> None:
        """List information about created S3 Tables catalog."""
        try:
            table_bucket_info = self._get_table_bucket_info()
            namespace_info = self._get_namespace_info()

            print(f"\nS3 Tables Configuration:")
            print(f"Table Bucket ARN: {table_bucket_info['table_bucket_arn']}")
            print(f"Namespace: {namespace_info['namespace']}")

            response = self.s3tables_client.list_tables(
                tableBucketARN=table_bucket_info["table_bucket_arn"],
                namespace=namespace_info["namespace"],
            )

            tables = response.get("tables", [])
            print(f"\nS3 Tables ({len(tables)}):")

            for table in tables:
                print(f"  - {table['name']}")
                print(f"    Format: {table.get('format', 'N/A')}")
                print(f"    Created: {table.get('createdAt', 'N/A')}")
                print()

        except Exception as e:
            logger.error(f"Error listing S3 Tables catalog info: {e}")


def main():
    """Main execution function."""
    try:
        creator = S3TablesCatalogCreator()

        success = creator.create_s3_tables_catalog()

        if success:
            print(f"\n✅ S3 Tables catalog creation completed successfully!")
            creator.list_catalog_info()
        else:
            print(f"\n❌ S3 Tables catalog creation failed!")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
