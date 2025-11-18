import google.generativeai as genai
import os
import logging

log = logging.getLogger(__name__)

class ExplainAgent:
    def __init__(self):
        """
        Initializes the Explain Agent and configures the Gemini model.
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
        log.info("Received request to explain code.")
        
        system_instructions = """
        You are a CoderLang Explanation Agent.
        Your sole purpose is to explain the code inside the <input_code> tags.
        
        You MUST explain the code I provide in the <input_code> tags.
        Do NOT explain any other program.
        """
        
        user_message = f"""
        <input_code>
        {code_string}
        </input_code>
        """
        
        # --- THE FIX ---
        messages = [
            {'role': 'user', 'parts': [system_instructions]},
            {'role': 'model', 'parts': ["OK. I am ready to explain the code you provide."]},
            {'role': 'user', 'parts': [user_message]}
        ]
        
        try:
            response = self.model.generate_content(messages)
            explanation = response.text.strip()
            log.info("Explanation successful.")
            return explanation
        except Exception as e:
            log.error(f"Explanation failed! Error: {e}")
            return f"An error occurred: {e}"