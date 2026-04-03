"""
Admin API Tests for Store Daily QA System
Tests for question and message management endpoints
"""

import pytest
from test_helpers import assert_question_response, assert_message_response


class TestQuestionManagement:
    """Test cases for question management endpoints"""

    def test_create_question(self, api_client, sample_question_data, test_data_tracker):
        """Test question creation"""
        response = api_client.post(
            "/api/admin/survey/questions", json=sample_question_data
        )
        assert response.status_code == 200

        data = response.json()
        assert "admin_survey_id" in data
        question_id = data["admin_survey_id"]

        test_data_tracker["admin_survey_questions"].append(question_id)

    def test_get_questions(self, api_client, sample_question_data, test_data_tracker):
        """Test getting questions list"""
        create_response = api_client.post(
            "/api/admin/survey/questions", json=sample_question_data
        )
        question_id = create_response.json()["admin_survey_id"]
        test_data_tracker["admin_survey_questions"].append(question_id)

        response = api_client.get("/api/admin/survey/questions")
        assert response.status_code == 200

        data = response.json()
        assert "questions" in data
        assert isinstance(data["questions"], list)

        created_question = next(
            (q for q in data["questions"] if q["admin_survey_id"] == question_id), None
        )
        assert created_question is not None
        assert_question_response(created_question)

    def test_get_question_detail(
        self, api_client, sample_question_data, test_data_tracker
    ):
        """Test getting question detail"""
        create_response = api_client.post(
            "/api/admin/survey/questions", json=sample_question_data
        )
        question_id = create_response.json()["admin_survey_id"]
        test_data_tracker["admin_survey_questions"].append(question_id)

        response = api_client.get(f"/api/admin/survey/questions/{question_id}")
        assert response.status_code == 200

        question = response.json()
        assert_question_response(question)
        assert question["question_text"] == sample_question_data["question_text"]

    def test_update_question(self, api_client, sample_question_data, test_data_tracker):
        """Test question update"""
        create_response = api_client.post(
            "/api/admin/survey/questions", json=sample_question_data
        )
        question_id = create_response.json()["admin_survey_id"]
        test_data_tracker["admin_survey_questions"].append(question_id)

        update_data = {
            "question_text": "LOCAL_API_TEST 更新された質問です",
            "question_type": "text",
            "is_active": False,
        }
        response = api_client.put(
            f"/api/admin/survey/questions/{question_id}", json=update_data
        )
        assert response.status_code == 200

        get_response = api_client.get(f"/api/admin/survey/questions/{question_id}")
        updated_question = get_response.json()
        assert updated_question["question_text"] == update_data["question_text"]

    def test_delete_question(self, api_client, sample_question_data, test_data_tracker):
        """Test question deletion (logical delete)"""
        create_response = api_client.post(
            "/api/admin/survey/questions", json=sample_question_data
        )
        question_id = create_response.json()["admin_survey_id"]
        test_data_tracker["admin_survey_questions"].append(question_id)

        response = api_client.delete(f"/api/admin/survey/questions/{question_id}")
        assert response.status_code == 200


class TestMessageManagement:
    """Test cases for message management endpoints"""

    def test_create_message(self, api_client, sample_message_data, test_data_tracker):
        """Test message creation"""
        response = api_client.post("/api/admin/messages", json=sample_message_data)
        assert response.status_code == 200

        data = response.json()
        assert "admin_messages_id" in data
        message_id = data["admin_messages_id"]

        test_data_tracker["admin_messages"].append(message_id)

    def test_get_messages(self, api_client, sample_message_data, test_data_tracker):
        """Test getting messages list"""
        create_response = api_client.post(
            "/api/admin/messages", json=sample_message_data
        )
        message_id = create_response.json()["admin_messages_id"]
        test_data_tracker["admin_messages"].append(message_id)

        response = api_client.get("/api/admin/messages")
        assert response.status_code == 200

        data = response.json()
        assert "messages" in data
        assert isinstance(data["messages"], list)

        created_message = next(
            (m for m in data["messages"] if m["admin_messages_id"] == message_id), None
        )
        assert created_message is not None
        assert_message_response(created_message)

    def test_get_message_detail(
        self, api_client, sample_message_data, test_data_tracker
    ):
        """Test getting message detail"""
        create_response = api_client.post(
            "/api/admin/messages", json=sample_message_data
        )
        message_id = create_response.json()["admin_messages_id"]
        test_data_tracker["admin_messages"].append(message_id)

        response = api_client.get(f"/api/admin/messages/{message_id}")
        assert response.status_code == 200

        message = response.json()
        assert_message_response(message)
        assert message["title"] == sample_message_data["title"]

    def test_update_message(self, api_client, sample_message_data, test_data_tracker):
        """Test message update"""
        create_response = api_client.post(
            "/api/admin/messages", json=sample_message_data
        )
        message_id = create_response.json()["admin_messages_id"]
        test_data_tracker["admin_messages"].append(message_id)

        update_data = {
            "title": "LOCAL_API_TEST 更新されたお知らせ",
            "content": "これは更新されたお知らせの内容です。",
            "is_active": False,
        }
        response = api_client.put(f"/api/admin/messages/{message_id}", json=update_data)
        assert response.status_code == 200

        get_response = api_client.get(f"/api/admin/messages/{message_id}")
        updated_message = get_response.json()
        assert updated_message["title"] == update_data["title"]

    def test_delete_message(self, api_client, sample_message_data, test_data_tracker):
        """Test message deletion (logical delete)"""
        create_response = api_client.post(
            "/api/admin/messages", json=sample_message_data
        )
        message_id = create_response.json()["admin_messages_id"]
        test_data_tracker["admin_messages"].append(message_id)

        response = api_client.delete(f"/api/admin/messages/{message_id}")
        assert response.status_code == 200
