import google.generativeai as genai
import os
import logging

log = logging.getLogger(__name__)

class TestGeneratorAgent:
    def __init__(self):
        """
        Initializes the Test Generator Agent and configures the Gemini model.
        """
        log.info("Initializing...")
        
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            log.error("GOOGLE_API_KEY not found.")
            raise ValueError("GOOGLE_API_KEY not found.")
        
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
        log.info("Model configured (gemini-2.5-pro).")
        
    def run(self, code_string: str) -> str:
        log.info("Received request to generate tests.")
        
        # --- THIS IS THE FIX ---
        # Updated prompt to generate simple, runnable tests instead of pytest.
        system_instructions = f"""
        You are a Test Generator Agent.
        Your sole purpose is to write *simple, runnable* Python tests for the code inside the <input_code> tags.
        
        You MUST write tests that can be executed directly by a Python interpreter.
        Do NOT use the `pytest` library.
        Use simple `assert` statements within test functions.
        
        To make the tests run, you MUST include a main execution block at the end, like:
        if __name__ == "__main__":
            # ... call your test functions here ...
            print("All tests passed!")
        
        Provide *only* the Python code for the tests, including the main block.
        Do not include markdown or '```python' wrappers.
        """
        
        user_message = f"""
        <input_code>
        {code_string}
        </input_code>
        """

        messages = [
            {'role': 'user', 'parts': [system_instructions]},
            {'role': 'model', 'parts': ["OK. I am ready to generate simple, runnable tests."]},
            {'role': 'user', 'parts': [user_message]}
        ]

        try:
            response = self.model.generate_content(messages)
            unit_tests = response.text
            unit_tests = unit_tests.strip().replace("```python", "").replace("```", "").strip()
            log.info("Test generation successful.")
            return unit_tests
        except Exception as e:
            log.error(f"Test generation failed! Error: {e}")
            return f"An error occurred: {e}"