import google.generativeai as genai
import os
import logging

log = logging.getLogger(__name__)

class DebuggingAgent:
    def __init__(self):
        """
        Initializes the Debugging Agent and configures the Gemini model.
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
        
    def run(self, code_string: str, error_message: str) -> str:
        log.info(f"Received request to fix error: {error_message}")
        
        system_prompt = f"""
        You are a CoderLang Debugging Agent.
        Your sole purpose is to fix the bug in the code inside the <input_code> tags,
        based on the provided error message.
        
        Provide *only* the fixed, complete Python code. No markdown.
        
        <input_code>
        {code_string}
        </input_code>
        
        Error Message: {error_message}
        """
        
        try:
            response = self.model.generate_content(system_prompt)
            fixed_code = response.text.strip().replace("```python", "").replace("```", "").strip()
            log.info("Debugging successful.")
            return fixed_code
        except Exception as e:
            log.error(f"Debugging failed! Error: {e}")
            return f"An error occurred: {e}"