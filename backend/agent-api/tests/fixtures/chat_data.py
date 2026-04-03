from routes.schema.chat import ChatMessageRequest


def get_sample_chat_request():
    return ChatMessageRequest(
        agent_type="hearing",
        message="今日の売上について教えてください",
        session_id="test-session-123",
        actor_id="U001",
    )


def get_sample_chat_response():
    return {
        "response": "今日の売上は好調です。前日比で10%増加しています。",
        "session_id": "test-session-123",
        "actor_id": "U001",
    }


def get_sample_chat_session():
    return {
        "session_id": "test-session-123",
        "survey_id": "survey-123",
        "user_cd": "U001",
        "str_cd": "S001",
        "messages": [
            {"role": "user", "content": "今日の売上について教えてください"},
            {"role": "assistant", "content": "今日の売上は好調です。"},
        ],
        "created_at": "2026-01-30T00:00:00",
        "updated_at": "2026-01-30T00:00:00",
    }
