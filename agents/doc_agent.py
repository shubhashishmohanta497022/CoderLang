import google.generativeai as genai
import os
import logging
from config import MODEL_NAME, SAFETY_SETTINGS

log = logging.getLogger(__name__)

class DocumentationAgent:
    def __init__(self):
        log.info("Initializing Documentation Agent...")
        
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            log.error("GOOGLE_API_KEY not found.")
            raise ValueError("GOOGLE_API_KEY not found.")
        
        genai.configure(api_key=api_key)
        
        self.model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            safety_settings=SAFETY_SETTINGS
        )
        
    def run(self, code_string: str = "", **kwargs) -> str:
        """
        Adds docstrings to code. 
        Uses **kwargs to handle variations in arguments (e.g., 'prompt', 'code').
        """
        log.info("Received request to document code.")

        # Fallback: If code_string is empty, check if the planner sent it as 'prompt' or 'code'
        if not code_string:
            code_string = kwargs.get('prompt', kwargs.get('code', ''))

        if not code_string:
            return "Error: No code provided to document."
        
        system_instructions = f"""
        You are a CoderLang Documentation Agent.
        Your sole purpose is to add Python docstrings (PEP 257) to the code provided.
        
        You MUST document the code I provide.
        Do NOT add any other functions or code.
        Provide *only* the Python code, now updated with your documentation.
        """
        
        user_message = f"""
        <input_code>
        {code_string}
        </input_code>
        """
        
        try:
            # Use strict list format for messages
            messages = [
                {'role': 'user', 'parts': [system_instructions]},
                {'role': 'model', 'parts': ["OK. I am ready to document the code."]},
                {'role': 'user', 'parts': [user_message]}
            ]
            
            response = self.model.generate_content(messages)
            documented_code = response.text
            
            # Clean up markdown
            documented_code = documented_code.strip()
            if documented_code.startswith("```"):
                documented_code = documented_code.replace("```python", "").replace("```", "").strip()

            log.info("Documentation successful.")
            return documented_code
        except Exception as e:
            log.error(f"Documentation failed! Error: {e}")
            return f"An error occurred: {e}"