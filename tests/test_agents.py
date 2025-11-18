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
# The DebuggingAgent requires more complex error mocking, so we skip it for simple unit tests.


@pytest.fixture(scope="module")
def mock_genai_model():
    """Fixture to mock the Gemini model response across agents."""
    with patch('google.generativeai.GenerativeModel') as MockModel:
        # Create a mock instance
        mock_instance = MockModel.return_value
        
        # Configure its generate_content method
        mock_response = MagicMock()
        mock_response.text = "Mocked Agent Output"
        mock_response.candidates = [MagicMock()] # For safety/grounding metadata checks
        
        mock_instance.generate_content.return_value = mock_response
        
        yield MockModel

def test_coding_agent_initialization():
    """Tests that the CodingAgent initializes without errors."""
    agent = CodingAgent()
    assert agent is not None

def test_coding_agent_runs_and_cleans_output(mock_genai_model):
    """Tests that CodingAgent can call run and cleans Markdown wrappers."""
    
    # 1. Setup mock to return code with markdown fences (The root cause of the previous crash)
    mock_genai_model.return_value.generate_content.return_value.text = 