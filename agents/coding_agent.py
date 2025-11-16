import google.generativeai as genai
import os

class CodingAgent:
    def __init__(self):
        """
        Initializes the Coding Agent and configures the Gemini model.
        """
        print("🤖 CodingAgent: Initializing...")
        
        # We need to configure the API key. 
        # This will be loaded by main.py
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found. Please set the environment variable.")
        
        genai.configure(api_key=api_key)
        
        # --- Copied from our notebook ---
        # Using gemini-2.5-pro as you selected
        self.model = genai.GenerativeModel(
            model_name='gemini-2.5-pro',
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
        )
        print("🤖 CodingAgent: Model configured (gemini-2.5-pro).")
        
    def run(self, prompt: str) -> str:
        """
        Runs the agent on a given prompt to generate code.
        """
        print(f"🤖 CodingAgent: Received prompt: {prompt}")
        
        # --- This is our perfected system prompt ---
        system_prompt = f"""
        You are a CoderLang Coding Agent.
        Your sole purpose is to write clean, effective, and correct 
        Python code based on a user's request.
        
        Provide *only* the Python code.
        Do not include any explanations, markdown, or '```python' wrappers.
        
        User Request: {prompt}
        """
        
        try:
            response = self.model.generate_content(system_prompt)
            generated_code = response.text
            print("🤖 CodingAgent: Code generation successful.")
            return generated_code
        except Exception as e:
            print(f"🤖 CodingAgent: ❌ Code generation failed!")
            print(f"Error: {e}")
            return f"An error occurred: {e}"