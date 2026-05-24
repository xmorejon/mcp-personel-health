import pytest

@pytest.fixture
def sample_health_data():
    return {
        "date": "2026-05-20",
        "averageHeartRate": 72,
        "steps": 3969,
        "weight": 86.2,
        "activities": [
            {
                "type": "WALKING",
                "distanceKm": 1.2
            }
        ]
    }

@pytest.fixture
def mock_agent_run(mocker):
    """Mocks the LLM agent's run method."""
    mock = mocker.patch("main.agent.run")
    return mock
