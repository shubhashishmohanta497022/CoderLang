import google.generativeai as genai
import os
import logging

log = logging.getLogger(__name__)

class SafetyAgent:
    def __init__(self):
        """
        Initializes the Safety Agent and configures the Gemini model.
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
        log.info("Received request to scan code.")
        
        system_instructions = f"""
        You are a CoderLang Safety Agent.
        Your sole purpose is to check the code inside the <input_code> tags.
        
        You MUST analyze the code I provide in the <input_code> tags.
        Do NOT hallucinate or invent risks.
        
        Unsafe operations include: 'os.remove', 'subprocess.run', 'eval', 'pickle'.
        
        Format your response as:
        Verdict: [SAFE or UNSAFE]
        Justification: [Your one-sentence justification]
        """
        
        user_message = f"""
        <input_code>
        {code_string}
        </input_code>
        """
        
        # --- THE FINAL FIX ---
        # We will build a list of messages and pass it 
        # directly to generate_content() instead of using start_chat().
        # This is more robust.
        
        messages = [
            {'role': 'user', 'parts': [system_instructions]},
            {'role': 'model', 'parts': ["OK. I am ready to scan the code."]},
            {'role': 'user', 'parts': [user_message]}
        ]
        
        try:
            # Pass the list directly
            response = self.model.generate_content(messages)
            verdict = response.text.strip()
            log.info("Scan successful.")
            return verdict
        except Exception as e:
            log.error(f"Scan failed! Error: {e}")
            return f"An error occurred: {e}"