def assert_response_structure(response_data, expected_fields):
    """レスポンスの構造を検証"""
    for field in expected_fields:
        assert field in response_data, f"Missing field: {field}"


def assert_question_response(question):
    """定型質問レスポンスの検証"""
    required_fields = [
        "admin_survey_id",
        "question_text",
        "question_type",
        "is_active",
        "created_at",
        "updated_at",
    ]
    assert_response_structure(question, required_fields)
    assert isinstance(question["admin_survey_id"], str)
    assert isinstance(question["question_text"], str)
    assert isinstance(question["is_active"], bool)


def assert_message_response(message):
    """お知らせレスポンスの検証"""
    required_fields = [
        "admin_messages_id",
        "title",
        "content",
        "is_active",
        "created_at",
        "updated_at",
    ]
    assert_response_structure(message, required_fields)


def assert_survey_response(survey):
    """サーベイレスポンスの検証"""
    required_fields = [
        "survey_id",
        "user_cd",
        "str_cd",
        "answers",
        "created_at",
        "updated_at",
    ]
    assert_response_structure(survey, required_fields)
    assert isinstance(survey["answers"], list)


def assert_insight_response(insight):
    """Insightsレスポンスの検証"""
    required_fields = [
        "id",
        "user_cd",
        "str_cd",
        "report_date",
        "status",
        "report_text",
        "session_id",
        "actor_id",
        "created_at",
        "updated_at",
    ]
    assert_response_structure(insight, required_fields)


def assert_error_response(response, expected_status_code, expected_error_field=None):
    """エラーレスポンスの検証"""
    assert response.status_code == expected_status_code

    data = response.json()
    assert "detail" in data or "message" in data or "error" in data

    if expected_error_field:
        if "error" in data:
            error_message = data["error"].get("message", "")
        else:
            error_message = data.get("detail", data.get("message", ""))
        assert expected_error_field in str(error_message).lower()


def assert_validation_error(response, field_name=None):
    """バリデーションエラーの検証（422 or 400）"""
    assert response.status_code in [400, 422]

    data = response.json()
    assert "detail" in data or "error" in data


def assert_not_found_error(response):
    """404エラーの検証"""
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data or "message" in data or "error" in data
