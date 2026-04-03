"""
Insights API Tests for Store Daily QA System
Tests for daily insights generation and retrieval endpoints
"""

import pytest
import uuid
from datetime import date, timedelta
from test_helpers import assert_insight_response


class TestDailyInsights:
    """Test cases for daily insights endpoints"""

    @pytest.mark.agent
    def test_generate_daily_insights(
        self, api_client, test_data_tracker, sample_survey_data
    ):
        """Test daily insights generation"""
        yesterday = (date.today() - timedelta(days=1)).isoformat()

        survey_data = {
            "survey_id": f"LOCAL_API_TEST_{uuid.uuid4()}",
            "answers": [
                {
                    "question_id": "q1",
                    "question_text": "LOCAL_API_TEST 今日の業務はいかがでしたか？",
                    "question_type": "rating",
                    "answer_value": "4",
                }
            ],
        }
        api_client.post("/api/survey/answers", json=survey_data)
        test_data_tracker["daily_survey_answers"].append(survey_data["survey_id"])

        insights_params = {
            "agent_type": "daily_summary",
            "prompt": "LOCAL_API_TEST 今日の業務についてインサイトを生成してください",
            "session_id": f"LOCAL_API_TEST_session_{uuid.uuid4()}",
            "report_date": yesterday,
        }

        response = api_client.post("/api/insights/daily/generate", json=insights_params)
        assert response.status_code == 200

        data = response.json()
        assert "response" in data
        assert "agent_type" in data
        assert "summary_id" in data
        assert data["agent_type"] == insights_params["agent_type"]
        assert isinstance(data["response"], str)

        query = f"report_date={yesterday}"
        get_response = api_client.get(f"/api/insights/daily?{query}")

        if get_response.status_code == 200:
            insight = get_response.json()
            test_data_tracker["daily_survey_summary"].append(insight["id"])

    def test_get_daily_insights(self, api_client, test_data_tracker):
        """Test getting daily insights"""
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        insights_params = {
            "agent_type": "daily_summary",
            "prompt": "LOCAL_API_TEST テスト用インサイト",
            "session_id": f"LOCAL_API_TEST_session_{uuid.uuid4()}",
            "report_date": yesterday,
        }

        api_client.post("/api/insights/daily/generate", json=insights_params)

        query = f"report_date={yesterday}"
        response = api_client.get(f"/api/insights/daily?{query}")

        if response.status_code == 200:
            insight = response.json()
            assert_insight_response(insight)
            test_data_tracker["daily_survey_summary"].append(insight["id"])

    def test_update_daily_insights(self, api_client, test_data_tracker):
        """Test updating daily insights"""
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        insights_params = {
            "agent_type": "daily_summary",
            "prompt": "LOCAL_API_TEST 更新テスト用インサイト",
            "session_id": f"LOCAL_API_TEST_session_{uuid.uuid4()}",
            "report_date": yesterday,
        }

        api_client.post("/api/insights/daily/generate", json=insights_params)

        query = f"report_date={yesterday}"
        get_response = api_client.get(f"/api/insights/daily?{query}")

        if get_response.status_code == 200:
            insight = get_response.json()
            insight_id = insight["id"]
            test_data_tracker["daily_survey_summary"].append(insight_id)

            update_data = {
                "report_date": yesterday,
                "status": "completed",
                "report_text": "LOCAL_API_TEST 更新されたレポート内容",
                "session_id": insights_params["session_id"],
            }
            response = api_client.put(
                f"/api/insights/daily/{insight_id}", json=update_data
            )
            assert response.status_code == 200

    def test_save_insights_feedback(self, api_client, test_data_tracker):
        """Test saving insights feedback"""
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        insights_params = {
            "agent_type": "daily_summary",
            "prompt": "LOCAL_API_TEST フィードバックテスト用インサイト",
            "session_id": f"LOCAL_API_TEST_session_{uuid.uuid4()}",
            "report_date": yesterday,
        }

        api_client.post("/api/insights/daily/generate", json=insights_params)

        query = f"report_date={yesterday}"
        get_response = api_client.get(f"/api/insights/daily?{query}")

        if get_response.status_code == 200:
            insight = get_response.json()
            insight_id = insight["id"]
            test_data_tracker["daily_survey_summary"].append(insight_id)

            feedback_data = {"user_feedback": "helpful"}
            response = api_client.put(
                f"/api/insights/daily/{insight_id}/feedback", json=feedback_data
            )
            assert response.status_code == 200

    def test_get_insights_history(self, api_client, test_data_tracker):
        """Test getting insights history"""
        import jwt
        
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        insights_params = {
            "agent_type": "daily_summary",
            "prompt": "LOCAL_API_TEST 履歴テスト用インサイト",
            "session_id": f"LOCAL_API_TEST_session_{uuid.uuid4()}",
            "report_date": yesterday,
        }

        api_client.post("/api/insights/daily/generate", json=insights_params)

        response = api_client.get("/api/insights/daily/history?page=1&limit=30")
        assert response.status_code == 200

        data = response.json()
        assert "insights" in data
        assert isinstance(data["insights"], list)

        token = api_client.default_headers["Authorization"].replace("Bearer ", "")
        payload = jwt.decode(token, options={"verify_signature": False})
        for insight in data["insights"]:
            if insight["user_cd"] == payload["sub"]:
                test_data_tracker["daily_survey_summary"].append(insight["id"])

    @pytest.mark.agent
    def test_regenerate_daily_insights(self, api_client, test_data_tracker):
        """Test regenerating existing daily insights"""
        today = date.today().isoformat()

        survey_data = {
            "survey_id": f"LOCAL_API_TEST_{uuid.uuid4()}",
            "answers": [
                {
                    "question_id": "q1",
                    "question_text": "LOCAL_API_TEST 再生成テスト用質問",
                    "question_type": "rating",
                    "answer_value": "5",
                }
            ],
        }
        api_client.post("/api/survey/answers", json=survey_data)
        test_data_tracker["daily_survey_answers"].append(survey_data["survey_id"])

        insights_params = {
            "agent_type": "daily_summary",
            "prompt": "LOCAL_API_TEST 再生成テスト用インサイト",
            "session_id": f"LOCAL_API_TEST_session_{uuid.uuid4()}",
            "report_date": today,
        }

        first_response = api_client.post(
            "/api/insights/daily/generate", json=insights_params
        )
        assert first_response.status_code == 200
        first_data = first_response.json()
        first_summary_id = first_data["summary_id"]

        query = f"report_date={today}"
        first_get_response = api_client.get(f"/api/insights/daily?{query}")
        assert first_get_response.status_code == 200
        first_insight = first_get_response.json()
        first_created_at = first_insight["created_at"]
        test_data_tracker["daily_survey_summary"].append(first_insight["id"])

        insights_params["session_id"] = f"LOCAL_API_TEST_session_{uuid.uuid4()}"
        second_response = api_client.post(
            "/api/insights/daily/generate", json=insights_params
        )
        assert second_response.status_code == 200
        second_data = second_response.json()
        second_summary_id = second_data["summary_id"]

        second_get_response = api_client.get(f"/api/insights/daily?{query}")
        assert second_get_response.status_code == 200
        second_insight = second_get_response.json()

        assert first_summary_id == second_summary_id, (
            "Summary ID should remain the same on regeneration"
        )
        assert first_created_at == second_insight["created_at"], (
            "Created timestamp should not change on regeneration"
        )
        assert first_insight["updated_at"] != second_insight["updated_at"], (
            "Updated timestamp should change on regeneration"
        )
        assert second_insight["session_id"] == insights_params["session_id"], (
            "Session ID should be updated"
        )
