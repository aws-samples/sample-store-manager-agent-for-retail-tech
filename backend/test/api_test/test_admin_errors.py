import pytest
from test_helpers import (
    assert_error_response,
    assert_validation_error,
    assert_not_found_error,
)


class TestQuestionManagementErrors:
    """定型質問管理の異常系テスト"""

    def test_create_question_missing_question_text(self, api_client):
        """question_text欠落でエラー"""
        data = {"question_type": "rating", "is_active": True}
        response = api_client.post("/api/admin/survey/questions", json=data)
        assert_validation_error(response, "question_text")

    def test_create_question_missing_question_type(self, api_client):
        """question_type欠落でエラー"""
        data = {"question_text": "テスト質問", "is_active": True}
        response = api_client.post("/api/admin/survey/questions", json=data)
        assert_validation_error(response, "question_type")

    def test_create_question_empty_question_text(self, api_client):
        """空文字列のquestion_textでエラー"""
        data = {"question_text": "", "question_type": "rating", "is_active": True}
        response = api_client.post("/api/admin/survey/questions", json=data)
        assert response.status_code in [400, 422]

    def test_create_question_invalid_question_type(self, api_client):
        """不正なquestion_typeでエラー"""
        data = {
            "question_text": "テスト質問",
            "question_type": "invalid_type",
            "is_active": True,
        }
        response = api_client.post("/api/admin/survey/questions", json=data)
        assert response.status_code in [400, 422]

    def test_get_nonexistent_question(self, api_client):
        """存在しない質問IDで404"""
        response = api_client.get("/api/admin/survey/questions/nonexistent-id")
        assert_not_found_error(response)

    def test_update_nonexistent_question(self, api_client):
        """存在しない質問IDで更新時404"""
        data = {
            "question_text": "更新テスト",
            "question_type": "rating",
            "is_active": True,
        }
        response = api_client.put(
            "/api/admin/survey/questions/nonexistent-id", json=data
        )
        assert_not_found_error(response)

    def test_delete_nonexistent_question(self, api_client):
        """存在しない質問IDで削除時404"""
        response = api_client.delete("/api/admin/survey/questions/nonexistent-id")
        assert_not_found_error(response)


class TestMessageManagementErrors:
    """お知らせ管理の異常系テスト"""

    def test_create_message_missing_title(self, api_client):
        """title欠落でエラー"""
        data = {"content": "テスト内容", "is_active": True}
        response = api_client.post("/api/admin/messages", json=data)
        assert_validation_error(response, "title")

    def test_create_message_missing_content(self, api_client):
        """content欠落でエラー"""
        data = {"title": "テストタイトル", "is_active": True}
        response = api_client.post("/api/admin/messages", json=data)
        assert_validation_error(response, "content")

    def test_create_message_empty_title(self, api_client):
        """空文字列のtitleでエラー"""
        data = {"title": "", "content": "テスト内容", "is_active": True}
        response = api_client.post("/api/admin/messages", json=data)
        assert response.status_code in [400, 422]

    def test_get_nonexistent_message(self, api_client):
        """存在しない通知IDで404"""
        response = api_client.get("/api/admin/messages/nonexistent-id")
        assert_not_found_error(response)

    def test_update_nonexistent_message(self, api_client):
        """存在しない通知IDで更新時404"""
        data = {"title": "更新テスト", "content": "更新内容", "is_active": True}
        response = api_client.put("/api/admin/messages/nonexistent-id", json=data)
        assert_not_found_error(response)

    def test_delete_nonexistent_message(self, api_client):
        """存在しない通知IDで削除時404"""
        response = api_client.delete("/api/admin/messages/nonexistent-id")
        assert_not_found_error(response)
