import pytest
from datetime import datetime
from utils.insights_service import InsightsService
from utils.exceptions import NotFoundException
from utils.auth import CurrentUser


INSIGHT_ID = "insight-001"
STR_CD = "store_001"


def _make_current_user() -> CurrentUser:
    return CurrentUser(
        user_cd="U001",
        actor_id="U001",
        str_cd=STR_CD,
        username="u",
        email="u@example.com",
    )


def _make_row() -> dict:
    return {
        "id": INSIGHT_ID,
        "user_cd": "U001",
        "str_cd": STR_CD,
        "report_date": "2026-01-30 00:00:00",
        "status": "completed",
        "report_text": "report",
        "session_id": "session-001",
        "actor_id": "U001",
        "created_at": "2026-01-30 00:00:00",
        "updated_at": "2026-01-30 00:00:00",
        "user_feedback": None,
    }


def _set_clause(query: str) -> str:
    return query[query.index("SET") : query.index("WHERE")]


def test_get_insight_by_id_filters_by_str_cd(mocker):
    mock_execute = mocker.patch(
        "utils.insights_service.execute_query_and_get_results",
        return_value=[_make_row()],
    )

    result = InsightsService().get_insight_by_id(INSIGHT_ID, STR_CD)

    query, params = mock_execute.call_args.args
    assert "WHERE id = ? AND str_cd = ?" in query
    assert params == [INSIGHT_ID, STR_CD]
    assert result["id"] == INSIGHT_ID
    assert result["report_date"] == datetime(2026, 1, 30)


def test_get_insight_by_id_other_store_raises_not_found(mocker):
    mocker.patch(
        "utils.insights_service.execute_query_and_get_results", return_value=[]
    )

    with pytest.raises(NotFoundException):
        InsightsService().get_insight_by_id(INSIGHT_ID, "other_store")


def test_save_daily_insights_update_scoped_by_str_cd(mocker):
    mock_select = mocker.patch(
        "utils.insights_service.execute_query_and_get_results",
        return_value=[_make_row()],
    )
    mock_update = mocker.patch("utils.insights_service.execute_query_with_pyathena")
    current_user = _make_current_user()

    InsightsService().save_daily_insights(
        current_user,
        INSIGHT_ID,
        datetime(2026, 1, 30),
        "completed",
        "new report",
        "session-001",
    )

    query, params = mock_update.call_args.args
    assert "WHERE id = %(insight_id)s AND str_cd = %(str_cd)s" in query
    assert "str_cd" not in _set_clause(query)
    assert params["str_cd"] == current_user.str_cd
    assert params["insight_id"] == INSIGHT_ID
    for call in mock_select.call_args_list:
        assert call.args[1] == [INSIGHT_ID, current_user.str_cd]


def test_save_daily_insights_other_store_raises_not_found(mocker):
    mocker.patch(
        "utils.insights_service.execute_query_and_get_results", return_value=[]
    )
    mock_update = mocker.patch("utils.insights_service.execute_query_with_pyathena")

    with pytest.raises(NotFoundException):
        InsightsService().save_daily_insights(
            _make_current_user(),
            INSIGHT_ID,
            datetime(2026, 1, 30),
            "completed",
            "new report",
            "session-001",
        )

    mock_update.assert_not_called()


def test_save_feedback_update_scoped_by_str_cd(mocker):
    mock_execute = mocker.patch(
        "utils.insights_service.execute_query_and_get_results",
        return_value=[_make_row()],
    )

    InsightsService().save_feedback(INSIGHT_ID, "good", STR_CD)

    update_calls = [
        call for call in mock_execute.call_args_list if "UPDATE" in call.args[0]
    ]
    assert len(update_calls) == 1
    query, params = update_calls[0].args
    assert "WHERE id = ? AND str_cd = ?" in query
    assert params == ["good", INSIGHT_ID, STR_CD]


def test_save_feedback_other_store_raises_not_found(mocker):
    mock_execute = mocker.patch(
        "utils.insights_service.execute_query_and_get_results", return_value=[]
    )

    with pytest.raises(NotFoundException):
        InsightsService().save_feedback(INSIGHT_ID, "good", "other_store")

    assert all("UPDATE" not in call.args[0] for call in mock_execute.call_args_list)
