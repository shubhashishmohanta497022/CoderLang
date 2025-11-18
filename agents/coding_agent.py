import google.generativeai as genai
import os
import logging 

log = logging.getLogger(__name__)

class CodingAgent:
    def __init__(self):
        """
        Initializes the Coding Agent and configures the Gemini model.
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
        
    def run(self, prompt: str) -> str:
        """
        Runs the agent on a given prompt to generate code.
        """
        log.info(f"Received prompt: {prompt}")
        
        system_prompt = f"""
        You are a CoderLang Coding Agent.
        Your sole purpose is to write clean, effective, and correct 
        Python code based on a user's request.
        
        You MUST follow all Python syntax rules and standard PEP 8
        style guides. Pay close attention to indentation.
        
        Provide *only* the raw, runnable Python code.
        Do NOT include any explanations, comments, or Markdown wrappers (e.g., '```python').
        
        User Request: {prompt}
        """
        
        try:
            response = self.model.generate_content(system_prompt)
            generated_code = response.text
            
            # --- FIX: Clean up markdown wrappers before returning ---
            generated_code = generated_code.strip()
            if generated_code.startswith("```python"):
                 generated_code = generated_code.replace("```python", "").strip()
            if generated_code.endswith("```"):
                 generated_code = generated_code.rstrip("`").strip()
            # ----------------------------------------------------

            log.info("Code generation successful.")
            return generated_code
        except Exception as e:
            log.error(f"Code generation failed! Error: {e}") 
            return f"An error occurred: {e}"