from routes.schema.admin import QuestionCreateRequest, MessageCreateRequest
from routes.schema.common import QuestionType


def get_sample_question_request():
    return QuestionCreateRequest(
        question_text="今日の売上はどうでしたか？",
        question_type=QuestionType.TEXT,
        display_order=1,
        is_required=True,
        options=None,
    )


def get_sample_question_response():
    return {
        "id": "question-123",
        "question_text": "今日の売上はどうでしたか？",
        "question_type": "text",
        "display_order": 1,
        "is_required": True,
        "options": None,
        "created_at": "2026-01-30T00:00:00",
        "updated_at": "2026-01-30T00:00:00",
    }


def get_sample_message_request():
    return MessageCreateRequest(
        title="システムメンテナンスのお知らせ",
        content="本日23:00-24:00にシステムメンテナンスを実施します。",
        message_type="info",
        is_active=True,
    )


def get_sample_message_response():
    return {
        "id": "message-123",
        "title": "システムメンテナンスのお知らせ",
        "content": "本日23:00-24:00にシステムメンテナンスを実施します。",
        "message_type": "info",
        "is_active": True,
        "created_at": "2026-01-30T00:00:00",
        "updated_at": "2026-01-30T00:00:00",
    }
