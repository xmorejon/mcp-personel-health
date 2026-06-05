import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def mock_tokeninfo(mocker, status_code=200, json_data=None):
    mock_response = mocker.Mock()
    mock_response.status_code = status_code
    mock_response.json.return_value = json_data or {}
    
    mock_client_instance = mocker.AsyncMock()
    mock_client_instance.get.return_value = mock_response
    mock_client_instance.__aenter__.return_value = mock_client_instance
    mock_client_instance.__aexit__.return_value = None
    
    mocker.patch("httpx.AsyncClient", return_value=mock_client_instance)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_handle_query_success(mocker):
    """Verify the endpoint parses the request correctly and returns the agent's text response."""
    mock_agent = mocker.patch("main.agent")
    mock_agent.run.return_value.text = "Your average heart rate is 72 bpm. That's a great resting rate!"
    
    mock_tokeninfo(mocker, 200, {
        "email": "xaviermorejonbalta@gmail.com",
        "expires_in": "3599"
    })
    
    payload = {"query": "What is my heart rate?"}
    headers = {"Authorization": "Bearer valid_token"}
    response = client.post("/ask", json=payload, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert data["response"] == "Your average heart rate is 72 bpm. That's a great resting rate!"
    
    mock_agent.run.assert_called_once_with("User ID: user_001\nQuery: What is my heart rate?")

def test_handle_query_validation_error(mocker):
    """Verify the endpoint enforces request schema validation."""
    mock_tokeninfo(mocker, 200, {
        "email": "xaviermorejonbalta@gmail.com",
        "expires_in": "3599"
    })
    headers = {"Authorization": "Bearer valid_token"}
    
    payload = {}
    response = client.post("/ask", json=payload, headers=headers)
    assert response.status_code == 422

def test_handle_query_internal_error(mocker):
    """Verify the endpoint handles internal agent errors gracefully."""
    mock_agent = mocker.patch("main.agent")
    mock_agent.run.side_effect = Exception("LLM connection timeout")
    
    mock_tokeninfo(mocker, 200, {
        "email": "xaviermorejonbalta@gmail.com",
        "expires_in": "3599"
    })
    
    payload = {"query": "What is my heart rate?"}
    headers = {"Authorization": "Bearer valid_token"}
    response = client.post("/ask", json=payload, headers=headers)
    
    assert response.status_code == 500
    assert "LLM connection timeout" in response.json()["detail"]

def test_auth_invalid_token(mocker):
    mock_tokeninfo(mocker, 400, {"error": "invalid_token"})
    response = client.post("/ask", json={"query": "test"}, headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401

def test_auth_expired_token(mocker):
    mock_tokeninfo(mocker, 200, {
        "email": "xaviermorejonbalta@gmail.com",
        "expires_in": "0"
    })
    response = client.post("/ask", json={"query": "test"}, headers={"Authorization": "Bearer expired"})
    assert response.status_code == 401

def test_auth_wrong_email(mocker):
    mock_tokeninfo(mocker, 200, {
        "email": "wrong@gmail.com",
        "expires_in": "3599"
    })
    response = client.post("/ask", json={"query": "test"}, headers={"Authorization": "Bearer token"})
    assert response.status_code == 401
    
def test_auth_missing_header():
    response = client.post("/ask", json={"query": "test"})
    assert response.status_code == 403
