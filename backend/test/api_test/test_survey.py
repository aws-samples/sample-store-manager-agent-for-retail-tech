"""
Survey API Tests for Store Daily QA System
Tests for survey answer submission and retrieval endpoints
"""

import pytest
from test_helpers import assert_survey_response


class TestSurveyAnswers:
    """Test cases for survey answer endpoints"""

    def test_save_survey_answer(
        self, api_client, sample_survey_data, test_data_tracker
    ):
        """Test survey answer submission"""
        response = api_client.post("/api/survey/answers", json=sample_survey_data)
        assert response.status_code == 200

        data = response.json()
        assert "survey_id" in data
        survey_id = data["survey_id"]

        test_data_tracker["daily_survey_answers"].append(survey_id)

    def test_get_survey_answers(
        self, api_client, sample_survey_data, test_data_tracker
    ):
        """Test getting survey answers list"""
        create_response = api_client.post(
            "/api/survey/answers", json=sample_survey_data
        )
        survey_id = create_response.json()["survey_id"]
        test_data_tracker["daily_survey_answers"].append(survey_id)

        response = api_client.get(f"/api/survey/answers/{survey_id}")
        assert response.status_code == 200

        created_survey = response.json()
        assert created_survey is not None
        assert_survey_response(created_survey)

    def test_get_survey_answer_detail(
        self, api_client, sample_survey_data, test_data_tracker
    ):
        """Test getting survey answer detail"""
        import jwt
        
        create_response = api_client.post(
            "/api/survey/answers", json=sample_survey_data
        )
        survey_id = create_response.json()["survey_id"]
        test_data_tracker["daily_survey_answers"].append(survey_id)

        response = api_client.get(f"/api/survey/answers/{survey_id}")
        assert response.status_code == 200

        survey = response.json()
        assert_survey_response(survey)
        
        token = api_client.default_headers["Authorization"].replace("Bearer ", "")
        payload = jwt.decode(token, options={"verify_signature": False})
        assert survey["user_cd"] == payload["sub"]

    def test_update_survey_answer(
        self, api_client, sample_survey_data, test_data_tracker
    ):
        """Test survey answer update"""
        create_response = api_client.post(
            "/api/survey/answers", json=sample_survey_data
        )
        survey_id = create_response.json()["survey_id"]
        test_data_tracker["daily_survey_answers"].append(survey_id)

        get_response = api_client.get(f"/api/survey/answers/{survey_id}")
        survey_data = get_response.json()

        answers_to_update = survey_data["answers"][:1]
        answers_to_update[0]["answer_value"] = "5"

        update_data = {"answers": answers_to_update}

        response = api_client.put(f"/api/survey/answers/{survey_id}", json=update_data)
        assert response.status_code == 200

        get_response = api_client.get(f"/api/survey/answers/{survey_id}")
        updated_survey = get_response.json()
        assert updated_survey["answers"][0]["answer_value"] == "5"
