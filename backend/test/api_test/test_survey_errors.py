import pytest
from test_helpers import (
    assert_error_response,
    assert_validation_error,
    assert_not_found_error,
)


class TestSurveyAnswersErrors:
    """サーベイ回答の異常系テスト"""

    def test_save_survey_missing_survey_id(self, api_client):
        """survey_id欠落でエラー"""
        data = {
            "answers": [{"question_id": "q1", "answer_value": "4"}],
        }
        response = api_client.post("/api/survey/answers", json=data)
        assert_validation_error(response, "survey_id")

    def test_save_survey_missing_answers(self, api_client):
        """answers欠落でエラー"""
        data = {
            "survey_id": "test_survey",
        }
        response = api_client.post("/api/survey/answers", json=data)
        assert_validation_error(response, "answers")

    def test_save_survey_empty_answers(self, api_client):
        """空配列のanswersでエラー"""
        data = {
            "survey_id": "test_survey",
            "answers": [],
        }
        response = api_client.post("/api/survey/answers", json=data)
        assert response.status_code in [400, 422]

    def test_save_survey_invalid_answer_structure(self, api_client):
        """不正なanswers構造でエラー"""
        data = {
            "survey_id": "test_survey",
            "answers": [{"invalid_field": "value"}],
        }
        response = api_client.post("/api/survey/answers", json=data)
        assert response.status_code in [400, 422]

    def test_get_nonexistent_survey(self, api_client):
        """存在しないsurvey_idで404"""
        response = api_client.get("/api/survey/answers/nonexistent-survey-id")
        assert_not_found_error(response)
