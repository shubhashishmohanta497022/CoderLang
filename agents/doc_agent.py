import google.generativeai as genai
import os
import logging

log = logging.getLogger(__name__)

class DocumentationAgent:
    def __init__(self):
        """
        Initializes the Documentation Agent and configures the Gemini model.
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
        log.info("Received request to document code.")
        
        system_prompt = f"""
        You are a CoderLang Documentation Agent.
        Your sole purpose is to add docstrings to the code inside the <input_code> tags.
        
        You MUST document the code I provide in the <input_code> tags.
        Do NOT add any other functions or code.
        
        Provide *only* the Python code, now updated with your documentation.
        
        <input_code>
        {code_string}
        </input_code>
        """
        
        try:
            response = self.model.generate_content(system_prompt)
            documented_code = response.text
            documented_code = documented_code.strip().replace("```python", "").replace("```", "").strip()
            log.info("Documentation successful.")
            return documented_code
        except Exception as e:
            log.error(f"Documentation failed! Error: {e}")
            return f"An error occurred: {e}"