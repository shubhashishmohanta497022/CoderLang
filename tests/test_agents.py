import pytest
import os
from unittest.mock import MagicMock, patch

# Note: We mock the genai client to prevent actual API calls during unit tests.

# Set a dummy API key to pass initialization checks
os.environ["GOOGLE_API_KEY"] = "DUMMY_KEY"

# Import agents only after setting the key, to avoid initialization errors
from agents.coding_agent import CodingAgent
from agents.safety_agent import SafetyAgent
from agents.test_generator_agent import TestGeneratorAgent
from agents.research_agent import ResearchAgent
from agents.translate_agent import TranslateAgent
from agents.explain_agent import ExplainAgent

@pytest.fixture(scope="module")
def mock_genai_model():
    """Fixture to mock the Gemini model response across agents."""
    with patch('google.generativeai.GenerativeModel') as MockModel:
        # Create a mock instance
        mock_instance = MockModel.return_value
        
        # 1. Configure basic generate_content response
        mock_response = MagicMock()
        mock_response.text = "Mocked Agent Output"
        
        # 2. Mock candidates for ResearchAgent grounding checks
        mock_candidate = MagicMock()
        # Simulate grounding metadata structure
        mock_candidate.grounding_metadata.search_entry_point.rendered_content = "Mock Search Result"
        mock_response.candidates = [mock_candidate] 
        
        mock_instance.generate_content.return_value = mock_response
        
        # 3. Configure start_chat and send_message for agents that use chat (Translate, Debug, etc.)
        mock_chat = MagicMock()
        mock_chat.send_message.return_value = mock_response
        mock_instance.start_chat.return_value = mock_chat
        
        yield MockModel

def test_coding_agent_initialization(mock_genai_model):
    """Tests that the CodingAgent initializes without errors."""
    agent = CodingAgent()
    assert agent is not None

def test_coding_agent_runs_and_cleans_output(mock_genai_model):
    """Tests that CodingAgent can call run and cleans Markdown wrappers."""
    
    # Setup mock to return code with markdown fences (simulating raw LLM output)
    mock_genai_model.return_value.generate_content.return_value.text = "```python\nprint('Hello World')\n```"
    
    agent = CodingAgent()
    result = agent.run("Write hello world")
    
    # Assert that the markdown was stripped by your fix
    assert result == "print('Hello World')"
    assert "```" not in result

def test_safety_agent_verdict(mock_genai_model):
    """Tests that SafetyAgent returns a verdict."""
    mock_genai_model.return_value.generate_content.return_value.text = "Verdict: SAFE\nJustification: No dangerous ops."
    
    agent = SafetyAgent()
    result = agent.run("print('test')")
    
    assert "Verdict: SAFE" in result

def test_test_generator_cleans_output(mock_genai_model):
    """Tests that TestGeneratorAgent cleans markdown wrappers."""
    mock_genai_model.return_value.generate_content.return_value.text = "```python\ndef test_main(): assert True\n```"
    
    agent = TestGeneratorAgent()
    result = agent.run("def main(): pass")
    
    assert result == "def test_main(): assert True"
    assert "```" not in result

def test_research_agent_runs(mock_genai_model):
    """Tests that ResearchAgent runs without crashing on metadata checks."""
    mock_genai_model.return_value.generate_content.return_value.text = "Python 3.11 release date info..."
    
    agent = ResearchAgent()
    result = agent.run("When was Python 3.11 released?")
    
    assert "Python 3.11" in result

def test_translate_agent_chat(mock_genai_model):
    """Tests TranslateAgent uses chat history and cleans output."""
    # Mock the chat response specifically for C++
    mock_genai_model.return_value.start_chat.return_value.send_message.return_value.text = "```cpp\nstd::cout << 'Hello';\n```"
    
    agent = TranslateAgent()
    result = agent.run("print('Hello')", "C++")
    
    assert result == "std::cout << 'Hello';"
    assert "```" not in result