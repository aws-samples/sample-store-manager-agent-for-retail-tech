import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import boto3
import pandas as pd
from strands import Agent
from strands.tools import tool
from bedrock_agentcore.memory import MemoryClient
from config import config

REGION = config.REGION
TABLE_BUCKET_ARN = config.TABLE_BUCKET_ARN
NAMESPACE = config.NAMESPACE
ATHENA_OUTPUT_LOCATION = config.ATHENA_OUTPUT_LOCATION
athena_client = boto3.client("athena", region_name=REGION)

logger = logging.getLogger(__name__)


def _get_catalog_name() -> str:
    if TABLE_BUCKET_ARN:
        table_bucket_name = TABLE_BUCKET_ARN.split("/")[-1]
        return f"s3tablescatalog/{table_bucket_name}"
    return ""


def _execute_athena_query(
    query: str, execution_parameters: Optional[list] = None
) -> Optional[str]:
    try:
        logger.info("Executing Athena query...")

        query_params = {
            "QueryString": query,
            "ResultConfiguration": {"OutputLocation": ATHENA_OUTPUT_LOCATION},
        }

        if execution_parameters:
            query_params["ExecutionParameters"] = execution_parameters

        response = athena_client.start_query_execution(**query_params)

        execution_id = response["QueryExecutionId"]
        logger.info(f"Query execution started: {execution_id}")
        return execution_id

    except Exception as e:
        logger.error(f"Error executing query: {e}")
        return None


def _wait_for_query_completion(execution_id: str) -> bool:
    try:
        logger.info(f"Waiting for query completion: {execution_id}")

        while True:
            response = athena_client.get_query_execution(QueryExecutionId=execution_id)

            status = response["QueryExecution"]["Status"]["State"]

            if status == "SUCCEEDED":
                logger.info("Query completed successfully")
                return True
            elif status in ["FAILED", "CANCELLED"]:
                error_reason = response["QueryExecution"]["Status"].get(
                    "StateChangeReason", "Unknown error"
                )
                logger.error(f"Query failed: {error_reason}")
                return False

            time.sleep(2)

    except Exception as e:
        logger.error(f"Error waiting for query completion: {e}")
        return False


def _get_query_results(execution_id: str) -> Optional[pd.DataFrame]:
    try:
        logger.info("Retrieving query results...")

        results = []
        next_token = None

        while True:
            if next_token:
                response = athena_client.get_query_results(
                    QueryExecutionId=execution_id, NextToken=next_token
                )
            else:
                response = athena_client.get_query_results(
                    QueryExecutionId=execution_id
                )

            if not results:
                column_info = response["ResultSet"]["ResultSetMetadata"]["ColumnInfo"]
                columns = [col["Name"] for col in column_info]

            rows = response["ResultSet"]["Rows"]
            if not results:
                rows = rows[1:]

            for row in rows:
                row_data = []
                for data in row["Data"]:
                    value = data.get("VarCharValue") or ""
                    row_data.append(value)
                results.append(row_data)

            next_token = response.get("NextToken")
            if not next_token:
                break

        if results:
            df = pd.DataFrame(results, columns=columns)
            logger.info(f"Retrieved {len(df)} rows with {len(df.columns)} columns")
            return df
        else:
            logger.warning("No data returned from query")
            return pd.DataFrame()

    except Exception as e:
        logger.error(f"Error retrieving query results: {e}")
        return None


def _calculate_change(
    current_value: Optional[float], previous_value: Optional[float]
) -> tuple[Optional[float], Optional[str]]:
    if previous_value is None or previous_value == 0 or current_value is None:
        return None, None

    change_percentage = ((current_value - previous_value) / previous_value) * 100
    change_direction = (
        "increase"
        if change_percentage > 0
        else "decrease"
        if change_percentage < 0
        else "no_change"
    )

    return round(change_percentage, 1), change_direction


def _retrieve_chat_history(
    memory_id: str, session_id: str, actor_id: str = "user", max_turns: int = 100
) -> list:
    try:
        memory_client = MemoryClient(region_name=REGION)

        turns = memory_client.get_last_k_turns(
            memory_id=memory_id, actor_id=actor_id, session_id=session_id, k=max_turns
        )

        return turns
    except Exception as e:
        logger.error(f"Failed to retrieve chat history: {e}")
        return []


@tool
def get_previous_day_survey_data(agent: Agent) -> str:
    """
    前日の店舗アンケートデータを取得します。
    
    このツールは、指定された店舗の前日のアンケート回答データを取得します。
    店舗コードはエージェントの状態から自動的に取得されます。
    
    Args:
        agent: エージェントインスタンス（自動注入）
    
    Returns:
        前日のsurveyデータのJSON文字列。以下の情報を含みます：
        - date: データの日付
        - total_records: レコード総数
        - survey_data: アンケートデータの配列
    """
    try:
        str_cd = agent.state.get("str_cd")
        
        catalog_name = _get_catalog_name()
        if not catalog_name:
            return "エラー: S3 Tables設定が見つかりません。"

        jst = ZoneInfo("Asia/Tokyo")
        now_jst = datetime.now(jst)
        yesterday = now_jst - timedelta(days=1)
        yesterday_date = yesterday.strftime("%Y-%m-%d")

        where_clause = f"WHERE DATE(a.created_at) = DATE('{yesterday_date}')"
        execution_params = []

        if str_cd:
            where_clause += " AND a.str_cd = ?"
            execution_params.append(str_cd)

        query = f"""
        SELECT 
            a.id,
            a.summary_id,
            a.survey_id,
            a.user_cd,
            a.str_cd,
            a.question_text,
            a.question_type,
            a.answer_value,
            a.options,
            a.created_at,
            a.updated_at
        FROM "{catalog_name}"."{NAMESPACE}".daily_survey_answers a
        {where_clause}
        ORDER BY a.created_at DESC, a.summary_id, a.id
        """

        logger.info(f"Executing query with params: {execution_params}")
        execution_id = _execute_athena_query(
            query, execution_params if execution_params else None
        )
        if not execution_id:
            return "エラー: Athenaクエリの実行に失敗しました。"

        if not _wait_for_query_completion(execution_id):
            return "エラー: Athenaクエリの完了待機に失敗しました。"

        df = _get_query_results(execution_id)
        if df is None:
            return "エラー: クエリ結果の取得に失敗しました。"

        if df.empty:
            return f"前日（{yesterday_date}）のsurveyデータは見つかりませんでした。"

        survey_records = df.to_dict("records")

        result_data = {
            "date": yesterday_date,
            "total_records": len(df),
            "survey_data": survey_records,
        }

        return json.dumps(result_data, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"Error getting previous day survey data: {e}")
        return f"エラー: 前日のsurveyデータ取得中に問題が発生しました - {str(e)}"


@tool
def get_store_sales_data(agent: Agent) -> str:
    """
    前日の店舗売上データを取得します。
    
    このツールは、指定された店舗の前日の売上実績データを取得します。
    店舗コードはエージェントの状態から自動的に取得されます。
    売上金額、来客数、購入件数、予算達成率などの情報を含みます。
    
    Args:
        agent: エージェントインスタンス（自動注入）
    
    Returns:
        前日の売上データのJSON文字列。以下の情報を含みます：
        - date: データの日付
        - store_performance: 店舗パフォーマンス情報
          - sales: 売上金額と前日比
          - customer_traffic: 来客数と前日比
          - purchase_transactions: 購入件数と前日比
          - purchase_rate: 購入率と前日比
    """
    try:
        str_cd = agent.state.get("str_cd")
        
        logger.info("Getting store sales data from Athena...")
        catalog_name = _get_catalog_name()
        if not catalog_name:
            return "エラー: S3 Tables設定が見つかりません。"

        jst = ZoneInfo("Asia/Tokyo")
        now_jst = datetime.now(jst)
        yesterday = now_jst - timedelta(days=1)
        day_before_yesterday = now_jst - timedelta(days=2)
        yesterday_date = yesterday.strftime("%Y-%m-%d")
        day_before_yesterday_date = day_before_yesterday.strftime("%Y-%m-%d")

        sales_where = ""
        traffic_where = ""
        budget_where = ""
        execution_params = []

        if str_cd:
            sales_where = "AND s.str_cd = ?"
            traffic_where = "AND t.str_cd = ?"
            budget_where = "AND b.str_cd = ?"
            execution_params = [str_cd, str_cd, str_cd]

        query = f"""
        WITH daily_sales AS (
            SELECT 
                DATE(s.sales_date_time) as sales_date,
                s.str_cd,
                SUM(CAST(s.sales_amount AS DOUBLE)) as total_sales_amount,
                COUNT(DISTINCT s.receipt_no) as purchase_transactions,
                SUM(CAST(s.customer_count AS BIGINT)) as purchase_customers
            FROM "{catalog_name}"."{NAMESPACE}".t_sales s
            WHERE DATE(s.sales_date_time) IN (DATE('{yesterday_date}'), DATE('{day_before_yesterday_date}'))
            {sales_where}
            GROUP BY DATE(s.sales_date_time), s.str_cd
        ),
        daily_traffic AS (
            SELECT 
                DATE(t.date) as traffic_date,
                t.str_cd,
                MAX(CAST(t.visitor_count AS DOUBLE)) as total_customers
            FROM "{catalog_name}"."{NAMESPACE}".t_daily_store_traffic t
            WHERE DATE(t.date) IN (DATE('{yesterday_date}'), DATE('{day_before_yesterday_date}'))
            {traffic_where}
            GROUP BY DATE(t.date), t.str_cd
        ),
        daily_budget AS (
            SELECT 
                DATE(b.date) as budget_date,
                b.str_cd,
                MAX(b.sales_budget) as sales_budget
            FROM "{catalog_name}"."{NAMESPACE}".t_str_daily_budget b
            WHERE DATE(b.date) IN (DATE('{yesterday_date}'), DATE('{day_before_yesterday_date}'))
            {budget_where}
            GROUP BY DATE(b.date), b.str_cd
        )
        SELECT 
            COALESCE(s.sales_date, t.traffic_date, b.budget_date) as date,
            COALESCE(s.str_cd, t.str_cd, b.str_cd) as str_cd,
            s.total_sales_amount,
            s.purchase_transactions,
            s.purchase_customers,
            t.total_customers,
            b.sales_budget
        FROM daily_sales s
        FULL OUTER JOIN daily_traffic t ON s.sales_date = t.traffic_date AND s.str_cd = t.str_cd
        FULL OUTER JOIN daily_budget b ON COALESCE(s.sales_date, t.traffic_date) = b.budget_date 
            AND COALESCE(s.str_cd, t.str_cd) = b.str_cd
        ORDER BY date DESC, str_cd
        """

        logger.info(f"Executing query with params: {execution_params}")
        execution_id = _execute_athena_query(
            query, execution_params if execution_params else None
        )
        if not execution_id:
            return "エラー: Athenaクエリの実行に失敗しました。"

        if not _wait_for_query_completion(execution_id):
            return "エラー: Athenaクエリの完了待機に失敗しました。"

        df = _get_query_results(execution_id)
        if df is None:
            return "エラー: クエリ結果の取得に失敗しました。"

        if df.empty:
            return f"前日（{yesterday_date}）および前々日（{day_before_yesterday_date}）の売上データは見つかりませんでした。"

        yesterday_data = df[df["date"] == yesterday_date]
        day_before_yesterday_data = df[df["date"] == day_before_yesterday_date]

        if yesterday_data.empty:
            return f"前日（{yesterday_date}）の売上データは見つかりませんでした。"

        yesterday_row = yesterday_data.iloc[0] if len(yesterday_data) > 0 else None
        day_before_yesterday_row = (
            day_before_yesterday_data.iloc[0]
            if len(day_before_yesterday_data) > 0
            else None
        )

        def safe_float(value):
            try:
                return float(value) if value and str(value).strip() != "" else None
            except (ValueError, TypeError):
                return None

        sales_amount = (
            safe_float(yesterday_row["total_sales_amount"])
            if yesterday_row is not None
            else None
        )
        customer_count = (
            safe_float(yesterday_row["total_customers"])
            if yesterday_row is not None
            else None
        )
        purchase_transactions = (
            safe_float(yesterday_row["purchase_transactions"])
            if yesterday_row is not None
            else None
        )
        sales_budget = (
            safe_float(yesterday_row["sales_budget"])
            if yesterday_row is not None
            else None
        )

        prev_sales_amount = (
            safe_float(day_before_yesterday_row["total_sales_amount"])
            if day_before_yesterday_row is not None
            else None
        )
        prev_customer_count = (
            safe_float(day_before_yesterday_row["total_customers"])
            if day_before_yesterday_row is not None
            else None
        )
        prev_purchase_transactions = (
            safe_float(day_before_yesterday_row["purchase_transactions"])
            if day_before_yesterday_row is not None
            else None
        )

        purchase_rate = (
            (purchase_transactions / customer_count * 100)
            if customer_count and customer_count > 0 and purchase_transactions
            else None
        )
        prev_purchase_rate = (
            (prev_purchase_transactions / prev_customer_count * 100)
            if prev_customer_count
            and prev_customer_count > 0
            and prev_purchase_transactions
            else None
        )

        target_achievement = (
            (sales_amount / sales_budget * 100)
            if sales_budget and sales_budget > 0 and sales_amount
            else None
        )

        sales_change, sales_direction = _calculate_change(
            sales_amount, prev_sales_amount
        )
        customer_change, customer_direction = _calculate_change(
            customer_count, prev_customer_count
        )
        transaction_change, transaction_direction = _calculate_change(
            purchase_transactions, prev_purchase_transactions
        )
        purchase_rate_change, purchase_rate_direction = _calculate_change(
            purchase_rate, prev_purchase_rate
        )

        missing_data = []
        if sales_amount is None:
            missing_data.append("売上金額")
        if customer_count is None:
            missing_data.append("来客数")
        if purchase_transactions is None:
            missing_data.append("購入件数")
        if sales_budget is None:
            missing_data.append("予算金額")
        if day_before_yesterday_row is None:
            missing_data.append("前々日データ（前日比計算不可）")

        result_data = {
            "date": yesterday_date,
            "store_performance": {
                "sales": {
                    "amount": int(sales_amount) if sales_amount else None,
                    "currency": "JPY",
                    "change_percentage": sales_change,
                    "change_direction": sales_direction,
                    "target_achievement_percentage": round(target_achievement, 1)
                    if target_achievement
                    else None,
                },
                "customer_traffic": {
                    "count": int(customer_count) if customer_count else None,
                    "change_percentage": customer_change,
                    "change_direction": customer_direction,
                },
                "purchase_transactions": {
                    "count": int(purchase_transactions)
                    if purchase_transactions
                    else None,
                    "change_percentage": transaction_change,
                    "change_direction": transaction_direction,
                },
                "purchase_rate": {
                    "percentage": round(purchase_rate, 1) if purchase_rate else None,
                    "change_percentage": purchase_rate_change,
                    "change_direction": purchase_rate_direction,
                },
            },
            "metadata": {
                "generated_at": datetime.now().isoformat() + "Z",
                "data_source": "athena_s3_tables",
                "missing_data": missing_data,
                "description": "前日の店舗売上データ（実データ、前日比計算済み）",
            },
        }

        logger.info(f"Sales data retrieved for {yesterday_date}")
        return json.dumps(result_data, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"Error getting store sales data: {e}")
        return f"エラー: 店舗売上データ取得中に問題が発生しました - {str(e)}"
