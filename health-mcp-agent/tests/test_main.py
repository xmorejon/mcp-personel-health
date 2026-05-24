import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_handle_query_success(mocker):
    """Verify the endpoint parses the request correctly and returns the agent's text response."""
    # Mock the initialized agent in main.py
    mock_agent = mocker.patch("main.agent")
    mock_agent.run.return_value.text = "Your average heart rate is 72 bpm. That's a great resting rate!"
    
    payload = {
        "query": "What is my heart rate?",
        "userId": "user123"
    }
    
    response = client.post("/", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert data["response"] == "Your average heart rate is 72 bpm. That's a great resting rate!"
    
    # Verify the agent was called with the combined context string
    mock_agent.run.assert_called_once_with("User ID: user123\nQuery: What is my heart rate?")

def test_handle_query_validation_error():
    """Verify the endpoint enforces request schema validation."""
    # Missing userId
    payload = {
        "query": "What is my heart rate?"
    }
    response = client.post("/", json=payload)
    assert response.status_code == 422  # Unprocessable Entity
    
    # Missing query
    payload2 = {
        "userId": "user123"
    }
    response2 = client.post("/", json=payload2)
    assert response2.status_code == 422

def test_handle_query_internal_error(mocker):
    """Verify the endpoint handles internal agent errors gracefully."""
    mock_agent = mocker.patch("main.agent")
    mock_agent.run.side_effect = Exception("LLM connection timeout")
    
    payload = {
        "query": "What is my heart rate?",
        "userId": "user123"
    }
    
    response = client.post("/", json=payload)
    
    assert response.status_code == 500
    assert "LLM connection timeout" in response.json()["detail"]
