from datetime import date
from routes.schema.insights import InsightGenerateRequest


def get_sample_insight_request():
    return InsightGenerateRequest(
        agent_type="daily_summary",
        prompt="今日の売上とサーベイ結果を分析してください",
        session_id="insight-session-123",
        actor_id="U001",
        user_cd="U001",
        str_cd="S001",
        report_date=date(2026, 1, 30),
    )


def get_sample_insight_response():
    return {
        "id": "insight-123",
        "user_cd": "U001",
        "str_cd": "S001",
        "report_date": "2026-01-30",
        "report_text": "本日の売上は好調で、前日比10%増加しました。",
        "status": "draft",
        "user_feedback": None,
        "created_at": "2026-01-30T00:00:00",
        "updated_at": "2026-01-30T00:00:00",
    }


def get_sample_insights_list():
    return [
        {
            "id": "insight-001",
            "user_cd": "U001",
            "str_cd": "S001",
            "report_date": "2026-01-30",
            "created_at": "2026-01-30T00:00:00",
            "updated_at": "2026-01-30T00:00:00",
        },
        {
            "id": "insight-002",
            "user_cd": "U001",
            "str_cd": "S001",
            "report_date": "2026-01-29",
            "created_at": "2026-01-29T00:00:00",
            "updated_at": "2026-01-29T00:00:00",
        },
    ]
