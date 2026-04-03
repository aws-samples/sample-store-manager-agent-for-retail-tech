#!/usr/bin/env python3
"""
S3 Tables test data insertion script.
Inserts minimal test data for store agent testing.
"""

import boto3
import json
import time
import uuid
from datetime import datetime, timedelta
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class S3TablesTestDataInserter:
    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.athena_client = boto3.client("athena")

        s3_tables_config = self.config.get("s3_tables", {})
        self.table_bucket_arn = s3_tables_config.get("table_bucket_arn")
        self.namespace = s3_tables_config.get("namespace", "store_data")

        athena_config = self.config.get("athena", {})
        self.workgroup = athena_config.get("workgroup", "primary")
        self.output_location = athena_config.get("output_location")

        if self.table_bucket_arn:
            self.table_bucket_name = self.table_bucket_arn.split("/")[-1]
            self.catalog_name = f"s3tablescatalog/{self.table_bucket_name}"

        # Calculate dates
        today = datetime.now().date()
        self.yesterday = today - timedelta(days=1)
        self.day_before_yesterday = today - timedelta(days=2)

        self.store_id = "test_store_001"
        self.user_id = "test_user_001"
        self.user_id_2 = "test_user_002"
        self.survey_id_1 = str(uuid.uuid4())
        self.survey_id_2 = str(uuid.uuid4())
        self.chat_id_1 = str(uuid.uuid4())
        self.chat_id_2 = str(uuid.uuid4())

    def _load_config(self, config_path: str) -> dict:
        with open(config_path, "r") as f:
            return json.load(f)

    def _execute_query(self, query: str) -> str:
        response = self.athena_client.start_query_execution(
            QueryString=query,
            WorkGroup=self.workgroup,
            ResultConfiguration={"OutputLocation": self.output_location},
        )

        execution_id = response["QueryExecutionId"]

        while True:
            result = self.athena_client.get_query_execution(
                QueryExecutionId=execution_id
            )
            status = result["QueryExecution"]["Status"]["State"]

            if status in ["SUCCEEDED", "FAILED", "CANCELLED"]:
                break
            time.sleep(1)

        if status != "SUCCEEDED":
            error_reason = result["QueryExecution"]["Status"].get(
                "StateChangeReason", "Unknown error"
            )
            raise Exception(f"Query failed: {error_reason}")

        return execution_id

    def _to_date_string(self, date_obj):
        return date_obj.isoformat()

    def _get_current_timestamp(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    def insert_survey_data(self):
        current_time = self._get_current_timestamp()

        # query = f"""
        # INSERT INTO "{self.catalog_name}"."{self.namespace}"."daily_survey_summary"
        # (id, user_cd, str_cd, report_date, status, report_text, agentcore_memory_id, session_id, actor_id, user_feedback, supplement_comment, created_at, updated_at)
        # VALUES
        # ('{self.survey_id_1}', '{self.user_id}', '{self.store_id}', DATE '{self._to_date_string(self.yesterday)}', 'completed', 'テスト用レポートテキスト', 'memory-test-001', 'session-test-001', 'actor-test-001', 'テスト用フィードバック', '', TIMESTAMP '{current_time}', TIMESTAMP '{current_time}')
        # """
        # self._execute_query(query)
        # logger.info("Inserted daily_survey_summary data")

        query = f"""
        INSERT INTO "{self.catalog_name}"."{self.namespace}"."daily_survey_answers" 
        (id, summary_id, survey_id, user_cd, str_cd, question_text, question_type, answer_value, options, created_at, updated_at)
        VALUES 
        ('{str(uuid.uuid4())}', NULL, 'a2248533-eb27-44c6-8863-c4cea99dbb35', '{self.user_id}', '{self.store_id}', 'サービスの満足度はいかがでしたか？', 'rating', '5', '', TIMESTAMP '{self.yesterday.isoformat()} 10:00:00.000', TIMESTAMP '{self.yesterday.isoformat()} 10:00:00.000'),
        ('{str(uuid.uuid4())}', NULL, 'a2248533-eb27-44c6-8863-c4cea99dbb35', '{self.user_id}', '{self.store_id}', 'ご意見をお聞かせください', 'text', 'とても良いサービスでした', '', TIMESTAMP '{self.yesterday.isoformat()} 10:00:00.000', TIMESTAMP '{self.yesterday.isoformat()} 10:00:00.000'),
        ('{str(uuid.uuid4())}', NULL, 'a2248533-eb27-44c6-8863-c4cea99dbb35', '{self.user_id}', '{self.store_id}', 'comment', 'text', 'test comment', '', TIMESTAMP '{self.yesterday.isoformat()} 10:00:00.000', TIMESTAMP '{self.yesterday.isoformat()} 10:00:00.000'),
        ('{str(uuid.uuid4())}', NULL, 'a2248533-eb27-44c6-8863-c4cea99dbb35', '{self.user_id_2}', '{self.store_id}', 'サービスの満足度はいかがでしたか？', 'rating', '5', '', TIMESTAMP '{self.yesterday.isoformat()} 10:00:00.000', TIMESTAMP '{self.yesterday.isoformat()} 10:00:00.000'),
        ('{str(uuid.uuid4())}', NULL, 'a2248533-eb27-44c6-8863-c4cea99dbb35', '{self.user_id_2}', '{self.store_id}', 'ご意見をお聞かせください', 'text', 'とても良いサービスでした', '', TIMESTAMP '{self.yesterday.isoformat()} 10:00:00.000', TIMESTAMP '{self.yesterday.isoformat()} 10:00:00.000'),
        ('{str(uuid.uuid4())}', NULL, 'a2248533-eb27-44c6-8863-c4cea99dbb35', '{self.user_id_2}', '{self.store_id}', 'comment', 'text', 'test comment', '', TIMESTAMP '{self.yesterday.isoformat()} 10:00:00.000', TIMESTAMP '{self.yesterday.isoformat()} 10:00:00.000')
        """
        self._execute_query(query)
        logger.info("Inserted daily_survey_answers data")

    def insert_survey_data_admin(self):
        admin_store_id = "admin"
        admin_user_id = "system_user_001"
        admin_user_id_2 = "system_user_002"

        query = f"""
        INSERT INTO "{self.catalog_name}"."{self.namespace}"."daily_survey_answers" 
        (id, summary_id, survey_id, user_cd, str_cd, question_text, question_type, answer_value, options, created_at, updated_at)
        VALUES 
        ('{str(uuid.uuid4())}', NULL, 'a2248533-eb27-44c6-8863-c4cea99dbb35', '{admin_user_id}', '{admin_store_id}', 'サービスの満足度はいかがでしたか？', 'rating', '5', '', TIMESTAMP '{self.yesterday.isoformat()} 10:00:00.000', TIMESTAMP '{self.yesterday.isoformat()} 10:00:00.000'),
        ('{str(uuid.uuid4())}', NULL, 'a2248533-eb27-44c6-8863-c4cea99dbb35', '{admin_user_id}', '{admin_store_id}', 'ご意見をお聞かせください', 'text', 'とても良いサービスでした', '', TIMESTAMP '{self.yesterday.isoformat()} 10:00:00.000', TIMESTAMP '{self.yesterday.isoformat()} 10:00:00.000'),
        ('{str(uuid.uuid4())}', NULL, 'a2248533-eb27-44c6-8863-c4cea99dbb35', '{admin_user_id}', '{admin_store_id}', 'comment', 'text', 'test comment', '', TIMESTAMP '{self.yesterday.isoformat()} 10:00:00.000', TIMESTAMP '{self.yesterday.isoformat()} 10:00:00.000'),
        ('{str(uuid.uuid4())}', NULL, 'a2248533-eb27-44c6-8863-c4cea99dbb35', '{admin_user_id_2}', '{admin_store_id}', 'サービスの満足度はいかがでしたか？', 'rating', '5', '', TIMESTAMP '{self.yesterday.isoformat()} 10:00:00.000', TIMESTAMP '{self.yesterday.isoformat()} 10:00:00.000'),
        ('{str(uuid.uuid4())}', NULL, 'a2248533-eb27-44c6-8863-c4cea99dbb35', '{admin_user_id_2}', '{admin_store_id}', 'ご意見をお聞かせください', 'text', 'とても良いサービスでした', '', TIMESTAMP '{self.yesterday.isoformat()} 10:00:00.000', TIMESTAMP '{self.yesterday.isoformat()} 10:00:00.000'),
        ('{str(uuid.uuid4())}', NULL, 'a2248533-eb27-44c6-8863-c4cea99dbb35', '{admin_user_id_2}', '{admin_store_id}', 'comment', 'text', 'test comment', '', TIMESTAMP '{self.yesterday.isoformat()} 10:00:00.000', TIMESTAMP '{self.yesterday.isoformat()} 10:00:00.000')
        """
        self._execute_query(query)
        logger.info("Inserted daily_survey_answers data for admin store")

    def insert_sales_data(self):
        current_time = self._get_current_timestamp()

        # t_sales
        query = f"""
        INSERT INTO "{self.catalog_name}"."{self.namespace}"."t_sales" 
        (terminal_no, receipt_no, str_cd, sales_date_time, sku, br_cd, item_cd, is_sale, sales_quantity, sales_cost, sales_amount, customer_count)
        VALUES 
        ('TERM001', 'REC001', '{self.store_id}', TIMESTAMP '{self.yesterday.isoformat()} 10:00:00.000', 'SKU001', 'BR001', 'ITEM001', '0', '10', 3000.0, 5000.0, '1'),
        ('TERM001', 'REC002', '{self.store_id}', TIMESTAMP '{self.yesterday.isoformat()} 14:00:00.000', 'SKU002', 'BR001', 'ITEM002', '0', '5', 2500.0, 5000.0, '1'),
        ('TERM001', 'REC003', '{self.store_id}', TIMESTAMP '{self.day_before_yesterday.isoformat()} 11:00:00.000', 'SKU001', 'BR001', 'ITEM001', '0', '8', 2400.0, 4000.0, '1'),
        ('TERM001', 'REC004', '{self.store_id}', TIMESTAMP '{self.day_before_yesterday.isoformat()} 15:00:00.000', 'SKU002', 'BR001', 'ITEM002', '0', '3', 1500.0, 3000.0, '1')
        """
        self._execute_query(query)
        logger.info("Inserted t_sales data")

        # t_daily_store_traffic
        query = f"""
        INSERT INTO "{self.catalog_name}"."{self.namespace}"."t_daily_store_traffic" 
        (str_cd, date, weather_code, low_temp, high_temp, visitor_count)
        VALUES 
        ('{self.store_id}', TIMESTAMP '{self.yesterday.isoformat()} 00:00:00.000', 1, '18', '22', '150'),
        ('{self.store_id}', TIMESTAMP '{self.day_before_yesterday.isoformat()} 00:00:00.000', 2, '15', '18', '120')
        """
        self._execute_query(query)
        logger.info("Inserted t_daily_store_traffic data")

        # t_str_daily_budget
        query = f"""
        INSERT INTO "{self.catalog_name}"."{self.namespace}"."t_str_daily_budget" 
        (str_cd, date, br_cd, sales_budget)
        VALUES 
        ('{self.store_id}', TIMESTAMP '{self.yesterday.isoformat()} 00:00:00.000', 'BR001', 12000.0),
        ('{self.store_id}', TIMESTAMP '{self.day_before_yesterday.isoformat()} 00:00:00.000', 'BR001', 10000.0)
        """
        self._execute_query(query)
        logger.info("Inserted t_str_daily_budget data")

    def insert_sales_data_admin(self):
        admin_store_id = "admin"

        # t_sales
        query = f"""
        INSERT INTO "{self.catalog_name}"."{self.namespace}"."t_sales" 
        (terminal_no, receipt_no, str_cd, sales_date_time, sku, br_cd, item_cd, is_sale, sales_quantity, sales_cost, sales_amount, customer_count)
        VALUES 
        ('TERM001', 'REC001', '{admin_store_id}', TIMESTAMP '{self.yesterday.isoformat()} 10:00:00.000', 'SKU001', 'BR001', 'ITEM001', '0', '10', 3000.0, 5000.0, '1'),
        ('TERM001', 'REC002', '{admin_store_id}', TIMESTAMP '{self.yesterday.isoformat()} 14:00:00.000', 'SKU002', 'BR001', 'ITEM002', '0', '5', 2500.0, 5000.0, '1'),
        ('TERM001', 'REC003', '{admin_store_id}', TIMESTAMP '{self.day_before_yesterday.isoformat()} 11:00:00.000', 'SKU001', 'BR001', 'ITEM001', '0', '8', 2400.0, 4000.0, '1'),
        ('TERM001', 'REC004', '{admin_store_id}', TIMESTAMP '{self.day_before_yesterday.isoformat()} 15:00:00.000', 'SKU002', 'BR001', 'ITEM002', '0', '3', 1500.0, 3000.0, '1')
        """
        self._execute_query(query)
        logger.info("Inserted t_sales data for admin store")

        # t_daily_store_traffic
        query = f"""
        INSERT INTO "{self.catalog_name}"."{self.namespace}"."t_daily_store_traffic" 
        (str_cd, date, weather_code, low_temp, high_temp, visitor_count)
        VALUES 
        ('{admin_store_id}', TIMESTAMP '{self.yesterday.isoformat()} 00:00:00.000', 1, '18', '22', '150'),
        ('{admin_store_id}', TIMESTAMP '{self.day_before_yesterday.isoformat()} 00:00:00.000', 2, '15', '18', '120')
        """
        self._execute_query(query)
        logger.info("Inserted t_daily_store_traffic data for admin store")

        # t_str_daily_budget
        query = f"""
        INSERT INTO "{self.catalog_name}"."{self.namespace}"."t_str_daily_budget" 
        (str_cd, date, br_cd, sales_budget)
        VALUES 
        ('{admin_store_id}', TIMESTAMP '{self.yesterday.isoformat()} 00:00:00.000', 'BR001', 12000.0),
        ('{admin_store_id}', TIMESTAMP '{self.day_before_yesterday.isoformat()} 00:00:00.000', 'BR001', 10000.0)
        """
        self._execute_query(query)
        logger.info("Inserted t_str_daily_budget data for admin store")

    def run(self):
        logger.info("Starting test data insertion")
        logger.info(f"Store ID: {self.store_id}")
        logger.info(f"Yesterday: {self.yesterday}")
        logger.info(f"Day before yesterday: {self.day_before_yesterday}")

        try:
            self.insert_survey_data()
            self.insert_sales_data()
            self.insert_survey_data_admin()
            self.insert_sales_data_admin()
            logger.info("Test data insertion completed successfully")
        except Exception as e:
            logger.error(f"Error during test data insertion: {e}")
            raise


if __name__ == "__main__":
    inserter = S3TablesTestDataInserter()
    inserter.run()
