import google.generativeai as genai
import os
import logging

log = logging.getLogger(__name__)

class TranslateAgent:
    def __init__(self):
        """
        Initializes the Translate Agent and configures the Gemini model.
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
        
    def run(self, code_string: str, target_language: str) -> str:
        log.info(f"Received request to translate to {target_language}")
        
        system_prompt = f"""
        You are a CoderLang Translation Agent.
        Your sole purpose is to translate the code inside the <input_code> tags
        into the specified target language.
        
        You MUST translate the code I provide in the <input_code> tags.
        Do NOT translate any other program.
        
        Provide *only* the translated code.
        
        <input_code>
        {code_string}
        </input_code>
        
        Target Language: {target_language}
        """
        
        try:
            response = self.model.generate_content(system_prompt)
            translated_code = response.text.strip()
            translated_code = translated_code.replace(f"```{target_language.lower()}", "").replace("```", "").strip()
            log.info("Code translation successful.")
            return translated_code
        except Exception as e:
            log.error(f"Code translation failed! Error: {e}")
            return f"An error occurred: {e}"