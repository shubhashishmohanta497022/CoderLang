import google.generativeai as genai
import os
import logging 
from config import MODEL_NAME, SAFETY_SETTINGS # Ensure config is used

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
            model_name=MODEL_NAME,
            safety_settings=SAFETY_SETTINGS
        )
        log.info(f"Model configured ({MODEL_NAME}).")
        
    def run(self, prompt: str, context: str = "") -> str:
        """
        Runs the agent on a given prompt to generate code.
        Accepts an optional 'context' argument to handle inputs from other agents.
        """
        log.info(f"Received prompt: {prompt}")
        
        # Combine prompt with context if provided
        full_user_request = prompt
        if context:
            log.info("Context provided, appending to prompt.")
            full_user_request += f"\n\n[Additional Context/Research]:\n{context}"

        system_prompt = f"""
        You are a CoderLang Coding Agent.
        Your sole purpose is to write clean, effective, and correct 
        Python code based on a user's request.
        
        You MUST follow all Python syntax rules and standard PEP 8
        style guides. Pay close attention to indentation.
        
        Provide *only* the raw, runnable Python code.
        Do NOT include any explanations, comments, or Markdown wrappers (e.g., '```python').
        
        User Request: {full_user_request}
        """
        
        try:
            response = self.model.generate_content(system_prompt)
            generated_code = response.text
            
            # Clean up markdown wrappers before returning
            generated_code = generated_code.strip()
            if generated_code.startswith("```python"):
                 generated_code = generated_code.replace("```python", "").strip()
            if generated_code.endswith("```"):
                 generated_code = generated_code.rstrip("`").strip()

            log.info("Code generation successful.")
            return generated_code
        except Exception as e:
            log.error(f"Code generation failed! Error: {e}") 
            return f"An error occurred: {e}"