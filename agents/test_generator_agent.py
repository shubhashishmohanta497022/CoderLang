import google.generativeai as genai
import os

class TestGeneratorAgent:
    def __init__(self):
        """
        Initializes the Test Generator Agent and configures the Gemini model.
        """
        print("🤖 TestGeneratorAgent: Initializing...")
        
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found. Please set the environment variable.")
        
        genai.configure(api_key=api_key)
        
        self.model = genai.GenerativeModel(
            model_name='gemini-2.5-pro',
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
        )
        print("🤖 TestGeneratorAgent: Model configured (gemini-2.5-pro).")
        
    def run(self, code_string: str) -> str:
        """
        Runs the agent to generate unit tests for the given code.
        """
        print(f"🤖 TestGeneratorAgent: Received request to generate tests.")
        
        # --- System prompt from our notebook ---
        system_prompt = f"""
        You are a Test Generator Agent.
        Your sole purpose is to write clear, concise, and effective 
        `pytest` compatible unit tests for the following Python code.
        
        Provide *only* the Python code for the tests.
        Do not include any explanations, markdown, or '```python' wrappers.
        
        Code to test:
        {code_string}
        """
        
        try:
            response = self.model.generate_content(system_prompt)
            unit_tests = response.text
            print("🤖 TestGeneratorAgent: Test generation successful.")
            return unit_tests
        except Exception as e:
            print(f"🤖 TestGeneratorAgent: ❌ Test generation failed!")
            print(f"Error: {e}")
            return f"An error occurred: {e}"