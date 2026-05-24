import pytest
from agent import get_agent
from prompts import SYSTEM_PROMPT

def test_agent_initialization(mocker):
    """Verify agent can initialize correctly when auth succeeds."""
    mock_default = mocker.patch("agent.default", return_value=("mock_creds", "mock_project"))
    mock_mcp = mocker.patch("agent.McpToolset")
    mock_agent_class = mocker.patch("agent.Agent")
    
    agent = get_agent()
    
    assert agent is not None
    mock_default.assert_called_once()
    mock_mcp.assert_called_once()
    mock_agent_class.assert_called_once()

def test_agent_voice_friendly_prompt():
    """Verify the system prompt explicitly restricts markdown and commands voice-friendly output."""
    prompt_lower = SYSTEM_PROMPT.lower()
    
    # Assert voice-friendly characteristics
    assert "voice assistant" in prompt_lower
    assert "no bullet points" in prompt_lower
    assert "markdown" in prompt_lower
    assert "tables" in prompt_lower
    
    # Assert conciseness instructions
    assert "concise" in prompt_lower
    assert "under 3 sentences" in prompt_lower
    assert "under 6 sentences" in prompt_lower
    
    # Assert tone instructions
    assert "warm" in prompt_lower
    assert "personal" in prompt_lower

def test_agent_refuses_write_operations(mocker):
    """Verify that the McpToolset is configured to refuse write operations."""
    mocker.patch("agent.default", return_value=("mock_creds", "mock_project"))
    mock_mcp = mocker.patch("agent.McpToolset")
    mocker.patch("agent.Agent")
    
    get_agent()
    
    call_kwargs = mock_mcp.call_args.kwargs
    assert "tool_filter" in call_kwargs
    allowed_tools = call_kwargs["tool_filter"]
    
    # Verify explicitly allowed read operations
    assert "get_document" in allowed_tools
    assert "list_documents" in allowed_tools
    assert "list_collections" in allowed_tools
    
    # Verify write operations are NOT allowed
    assert "create_document" not in allowed_tools
    assert "update_document" not in allowed_tools
    assert "delete_document" not in allowed_tools

def test_agent_handles_auth_error(mocker):
    """Verify that the agent instantiation propagates authentication errors gracefully."""
    mocker.patch("agent.default", side_effect=Exception("Failed to get default credentials"))
    
    with pytest.raises(Exception, match="Failed to get default credentials"):
        get_agent()

def test_agent_handles_empty_firestore_results(mocker):
    """Verify that an empty result is handled.
    In a real scenario with the LLM, we verify the prompt handles this via scenarios.
    """
    prompt_lower = SYSTEM_PROMPT.lower()
    assert "if data is missing, gently let the user know" in prompt_lower
