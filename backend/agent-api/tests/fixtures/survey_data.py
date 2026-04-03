from datetime import datetime
from routes.schema.survey import SurveyAnswerRequest, AnswerData
from routes.schema.common import QuestionType


def get_sample_survey_request():
    return SurveyAnswerRequest(
        survey_id="test-survey-123",
        user_cd="U001",
        str_cd="S001",
        answers=[
            AnswerData(
                question_id="q001",
                question_text="今日の売上はどうでしたか？",
                question_type=QuestionType.TEXT,
                answer_value="好調でした",
                options=None,
            ),
            AnswerData(
                question_id="q002",
                question_text="満足度を教えてください",
                question_type=QuestionType.RATING,
                answer_value="4",
                options=None,
            ),
        ],
    )


def get_sample_survey_response():
    return {
        "id": "answer-123",
        "survey_id": "test-survey-123",
        "user_cd": "U001",
        "str_cd": "S001",
        "question_text": "今日の売上はどうでしたか？",
        "question_type": "text",
        "answer_value": "好調でした",
        "options": None,
        "created_at": "2026-01-30T00:00:00",
        "updated_at": "2026-01-30T00:00:00",
    }


def get_sample_survey_list():
    return [
        {
            "survey_id": "survey-001",
            "user_cd": "U001",
            "str_cd": "S001",
            "created_at": "2026-01-30T00:00:00",
        },
        {
            "survey_id": "survey-002",
            "user_cd": "U001",
            "str_cd": "S001",
            "created_at": "2026-01-29T00:00:00",
        },
    ]
