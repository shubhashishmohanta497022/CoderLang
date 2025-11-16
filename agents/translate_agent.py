import google.generativeai as genai
import os

class TranslateAgent:
    def __init__(self):
        """
        Initializes the Translate Agent and configures the Gemini model.
        """
        print("🤖 TranslateAgent: Initializing...")
        
        # We assume the API key is already set by main.py
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found. Please set the environment variable.")
        
        genai.configure(api_key=api_key)
        
        # Using gemini-2.5-pro
        self.model = genai.GenerativeModel(
            model_name='gemini-2.5-pro',
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
        )
        print("🤖 TranslateAgent: Model configured (gemini-2.5-pro).")
        
    def run(self, code_string: str, target_language: str) -> str:
        """
        Runs the agent to translate code.
        """
        print(f"🤖 TranslateAgent: Received request to translate to {target_language}")
        
        # --- System prompt from our notebook ---
        system_prompt = f"""
        You are a CoderLang Translation Agent.
        Your sole purpose is to translate the provided Python code
        into the target language.
        
        Provide *only* the translated code.
        Do not include any explanations, markdown, or '```python' wrappers.
        
        ---
        Original Code (Python):
        {code_string}
        ---
        Target Language:
        {target_language}
        ---
        """
        
        try:
            response = self.model.generate_content(system_prompt)
            translated_code = response.text
            print("🤖 TranslateAgent: Code translation successful.")
            return translated_code
        except Exception as e:
            print(f"🤖 TranslateAgent: ❌ Code translation failed!")
            print(f"Error: {e}")
            return f"An error occurred: {e}"