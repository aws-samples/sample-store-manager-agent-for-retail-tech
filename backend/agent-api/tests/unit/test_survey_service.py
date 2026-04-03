import pytest
from unittest.mock import MagicMock
from utils.survey_service import SurveyService
from utils.exceptions import ValidationException
from utils.database import DatabaseException
from utils.auth import CurrentUser
from tests.fixtures.survey_data import get_sample_survey_request


def test_save_survey_answer_success(mocker):
    mocker.patch(
        "utils.database.get_catalog_info",
        return_value={"catalog_name": "test-catalog", "database_name": "test-db"},
    )
    mock_execute = mocker.patch(
        "utils.survey_service.execute_query_and_get_results", return_value=[]
    )

    service = SurveyService()
    request = get_sample_survey_request()
    current_user = CurrentUser(
        user_cd="test_user",
        actor_id="test_actor",
        str_cd="test_store",
        username="test_user",
        email="test@example.com"
    )

    result = service.save_survey_answer(request, current_user)

    assert result["message"] == "Survey answer saved successfully"
    assert result["survey_id"] == "test-survey-123"
    mock_execute.assert_called_once()


def test_save_survey_answer_database_error(mocker):
    mocker.patch(
        "utils.database.get_catalog_info",
        return_value={"catalog_name": "test-catalog", "database_name": "test-db"},
    )
    mocker.patch(
        "utils.database.execute_query_and_get_results",
        side_effect=DatabaseException("DB error"),
    )

    service = SurveyService()
    request = get_sample_survey_request()
    current_user = CurrentUser(
        user_cd="test_user",
        actor_id="test_actor",
        str_cd="test_store",
        username="test_user",
        email="test@example.com"
    )

    with pytest.raises(DatabaseException):
        service.save_survey_answer(request, current_user)


def test_get_survey_answers_success(mocker):
    mocker.patch(
        "utils.database.get_catalog_info",
        return_value={"catalog_name": "test-catalog", "database_name": "test-db"},
    )

    mocker.patch(
        "utils.survey_service.execute_query_and_get_results",
        side_effect=[
            [{"total_count": "2"}],
            [
                {
                    "survey_id": "survey-001",
                    "user_cd": "U001",
                    "str_cd": "S001",
                    "created_at": "2026-01-30 00:00:00",
                    "updated_at": "2026-01-30 00:00:00",
                    "answer_count": "1",
                }
            ],
        ],
    )

    service = SurveyService()
    current_user = CurrentUser(
        user_cd="test_user",
        actor_id="test_actor",
        str_cd="S001",
        username="test_user",
        email="test@example.com"
    )
    result = service.get_survey_answers(current_user, page=1, limit=30)

    assert "answers" in result
    assert "total_count" in result


def test_get_survey_answer_success(mocker):
    mocker.patch(
        "utils.database.get_catalog_info",
        return_value={"catalog_name": "test-catalog", "database_name": "test-db"},
    )

    mocker.patch(
        "utils.survey_service.execute_query_and_get_results",
        side_effect=[
            [
                {
                    "survey_id": "survey-123",
                    "user_cd": "U001",
                    "str_cd": "S001",
                    "created_at": "2026-01-30 00:00:00",
                    "updated_at": "2026-01-30 00:00:00",
                }
            ],
            [
                {
                    "question_id": "answer-123",
                    "question_text": "テスト質問",
                    "question_type": "text",
                    "answer_value": "テスト回答",
                    "options": None,
                }
            ],
        ],
    )

    service = SurveyService()
    result = service.get_survey_answer("survey-123")

    assert result.survey_id == "survey-123"
