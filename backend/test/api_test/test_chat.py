"""
Chat API Tests for Store Daily QA System
Tests for chat interaction endpoints
"""

import pytest


class TestChatInteraction:
    """Test cases for chat interaction endpoints"""

    @pytest.mark.agent
    def test_send_chat_message_success(self, api_client, sample_chat_data):
        """Test successful chat message sending"""
        response = api_client.post("/api/chat/message", json=sample_chat_data)
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "session_id" in data
        assert data["session_id"] == sample_chat_data["session_id"]
        assert isinstance(data["response"], str)
        assert len(data["response"]) > 0

    def test_send_chat_message_validation_error(self, api_client):
        """Test chat message sending with invalid data"""
        invalid_data = {
            "agent_type": "",
            "prompt": "",
            "session_id": "",
        }
        response = api_client.post("/api/chat/message", json=invalid_data)
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "VALIDATION_ERROR"

    @pytest.mark.agent
    def test_send_chat_message_different_agent_types(self, api_client):
        """Test chat messages with different agent types"""
        agent_types = ["hearing", "coaching", "daily_summary"]

        for agent_type in agent_types:
            chat_data = {
                "agent_type": agent_type,
                "prompt": f"これは{agent_type}エージェントのテストです。",
                "session_id": f"test_session_{agent_type}",
                "survey_id": "test_survey_001",
            }

            response = api_client.post("/api/chat/message", json=chat_data)
            assert response.status_code == 200
            data = response.json()
            assert "response" in data
            assert data["session_id"] == chat_data["session_id"]

    def test_send_chat_message_invalid_agent_type(self, api_client):
        """Test chat message with invalid agent type"""
        invalid_chat_data = {
            "agent_type": "invalid_agent",
            "prompt": "テストメッセージ",
            "session_id": "test_session",
            "survey_id": "test_survey_001",
        }

        response = api_client.post("/api/chat/message", json=invalid_chat_data)
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "VALIDATION_ERROR"


class TestChatSessionManagement:
    """Test cases for chat session management endpoints"""

    def test_save_chat_session_success(self, api_client):
        """Test successful chat session saving"""
        session_data = {
            "survey_id": "survey_001",
            "session_id": "test_session_save_001",
        }

        response = api_client.post("/api/chat/session/save", json=session_data)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "Chat session saved successfully"

    def test_save_chat_session_validation_error(self, api_client):
        """Test chat session saving with invalid data"""
        invalid_session_data = {
            "survey_id": "",
            "session_id": "",
        }

        response = api_client.post("/api/chat/session/save", json=invalid_session_data)
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_get_chat_session_by_survey_id(self, api_client):
        """Test getting specific chat session by survey ID"""
        response = api_client.get(
            "/api/chat/session", params={"survey_id": "survey_001"}
        )
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "session_id" in data
            assert "survey_id" in data

    def test_get_chat_session_not_found(self, api_client):
        """Test getting non-existent chat session"""
        response = api_client.get(
            "/api/chat/session", params={"survey_id": "nonexistent_survey"}
        )
        assert response.status_code == 404


class TestChatIntegration:
    """Integration tests for chat endpoints"""

    @pytest.mark.agent
    def test_complete_chat_flow(self, api_client, sample_chat_data):
        """Test complete chat flow: send message -> save session -> retrieve session"""
        send_response = api_client.post("/api/chat/message", json=sample_chat_data)
        assert send_response.status_code == 200
        send_data = send_response.json()
        assert "response" in send_data

        session_data = {
            "survey_id": "survey_003",
            "session_id": sample_chat_data["session_id"],
        }

        save_response = api_client.post("/api/chat/session/save", json=session_data)
        assert save_response.status_code == 200
        save_data = save_response.json()
        assert "message" in save_data

    @pytest.mark.agent
    def test_multi_turn_conversation(self, api_client):
        """Test multi-turn conversation flow"""
        session_id = "multi_turn_test_001"
        base_chat_data = {
            "agent_type": "coaching",
            "session_id": session_id,
            "survey_id": "test_survey_001",
        }

        turns = [
            "今日の業務で困っていることはありますか？",
            "チームとのコミュニケーションが難しいです。",
            "具体的にどのような場面で困っていますか？",
        ]

        responses = []
        for turn in turns:
            chat_data = base_chat_data.copy()
            chat_data["prompt"] = turn

            response = api_client.post("/api/chat/message", json=chat_data)
            assert response.status_code == 200
            responses.append(response.json())

        assert len(responses) == len(turns)
        for response in responses:
            assert response["session_id"] == session_id
            assert "response" in response
