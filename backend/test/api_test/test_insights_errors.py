import pytest
from test_helpers import (
    assert_error_response,
    assert_validation_error,
    assert_not_found_error,
)


class TestDailyInsightsErrors:
    """Insights管理の異常系テスト"""

    def test_generate_insights_missing_agent_type(self, api_client):
        """agent_type欠落でエラー"""
        data = {
            "prompt": "テストプロンプト",
        }
        response = api_client.post("/api/insights/daily/generate", json=data)
        assert_validation_error(response, "agent_type")

    def test_generate_insights_missing_prompt(self, api_client):
        """prompt欠落でエラー"""
        data = {
            "agent_type": "daily_summary",
        }
        response = api_client.post("/api/insights/daily/generate", json=data)
        assert_validation_error(response, "prompt")

    def test_generate_insights_empty_prompt(self, api_client):
        """空文字列のpromptでエラー"""
        data = {
            "agent_type": "daily_summary",
            "prompt": "",
        }
        response = api_client.post("/api/insights/daily/generate", json=data)
        assert response.status_code in [400, 422]

    def test_generate_insights_invalid_agent_type(self, api_client):
        """不正なagent_typeでエラー"""
        data = {
            "agent_type": "invalid_type",
            "prompt": "テストプロンプト",
        }
        response = api_client.post("/api/insights/daily/generate", json=data)
        assert response.status_code in [400, 422]

    def test_get_nonexistent_insights(self, api_client):
        """存在しないInsightsで404"""
        query = "report_date=2099-12-31"
        response = api_client.get(f"/api/insights/daily?{query}")
        assert_not_found_error(response)
