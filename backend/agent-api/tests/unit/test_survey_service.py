import pytest
from unittest.mock import MagicMock
from utils.survey_service import SurveyService
from utils.exceptions import ValidationException, NotFoundException
from utils.database import DatabaseException
from utils.auth import CurrentUser
from routes.schema.survey import SurveyAnswerUpdateRequest, AnswerData
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
    current_user = CurrentUser(
        user_cd="test_user",
        actor_id="test_actor",
        str_cd="S001",
        username="test_user",
        email="test@example.com"
    )
    result = service.get_survey_answer("survey-123", current_user)

    assert result.survey_id == "survey-123"


def _build_store_user(str_cd: str) -> CurrentUser:
    """Build a CurrentUser that belongs to the given store."""
    return CurrentUser(
        user_cd="test_user",
        actor_id="test_actor",
        str_cd=str_cd,
        username="test_user",
        email="test@example.com"
    )


def _build_update_request(question_id: str, answer_value: str) -> SurveyAnswerUpdateRequest:
    """Build an update request with a single text answer."""
    return SurveyAnswerUpdateRequest(
        answers=[
            AnswerData(
                question_id=question_id,
                question_text="Question",
                question_type="text",
                answer_value=answer_value,
                options=None,
            )
        ]
    )


def test_get_survey_answer_scopes_queries_by_store(mocker):
    mock_execute = mocker.patch(
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
            [],
        ],
    )

    service = SurveyService()
    service.get_survey_answer("survey-123", _build_store_user("S001"))

    assert mock_execute.call_count == 2
    summary_query, summary_params = mock_execute.call_args_list[0].args
    answers_query, answers_params = mock_execute.call_args_list[1].args
    assert "a.survey_id = ? AND a.str_cd = ?" in summary_query
    assert summary_params == ["survey-123", "S001"]
    assert "survey_id = ? AND str_cd = ?" in answers_query
    assert answers_params == ["survey-123", "S001"]


def test_get_survey_answer_other_store_raises_not_found(mocker):
    mock_execute = mocker.patch(
        "utils.survey_service.execute_query_and_get_results",
        return_value=[],
    )

    service = SurveyService()
    with pytest.raises(NotFoundException):
        service.get_survey_answer("survey-of-other-store", _build_store_user("S001"))

    mock_execute.assert_called_once()


def test_update_survey_answer_scopes_queries_by_store(mocker):
    mock_execute = mocker.patch(
        "utils.survey_service.execute_query_and_get_results",
        side_effect=[
            [{"user_cd": "U001", "str_cd": "S001"}],
            [],
        ],
    )

    service = SurveyService()
    result = service.update_survey_answer(
        "survey-123",
        _build_update_request("answer-1", "new value"),
        _build_store_user("S001"),
    )

    assert result["survey_id"] == "survey-123"
    assert mock_execute.call_count == 2
    find_query, find_params = mock_execute.call_args_list[0].args
    update_query, update_params = mock_execute.call_args_list[1].args
    assert "survey_id = ? AND str_cd = ?" in find_query
    assert find_params == ["survey-123", "S001"]
    assert '"id" = ?' in update_query
    assert "survey_id = ?" in update_query
    assert "str_cd = ?" in update_query
    assert update_params == ["new value", "answer-1", "survey-123", "S001"]


def test_update_survey_answer_other_store_raises_not_found(mocker):
    mock_execute = mocker.patch(
        "utils.survey_service.execute_query_and_get_results",
        return_value=[],
    )

    service = SurveyService()
    with pytest.raises(NotFoundException):
        service.update_survey_answer(
            "survey-of-other-store",
            _build_update_request("answer-1", "new value"),
            _build_store_user("S001"),
        )

    mock_execute.assert_called_once()
    find_query, _ = mock_execute.call_args.args
    assert "UPDATE" not in find_query
