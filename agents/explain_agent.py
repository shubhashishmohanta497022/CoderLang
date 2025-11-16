import google.generativeai as genai
import os

class ExplainAgent:
    def __init__(self):
        """
        Initializes the Explain Agent and configures the Gemini model.
        """
        print("🤖 ExplainAgent: Initializing...")
        
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found. Please set the environment variable.")
        
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
        print("🤖 ExplainAgent: Model configured (gemini-2.5-pro).")
        
    def run(self, code_string: str) -> str:
        """
        Runs the agent to explain the given code.
        """
        print(f"🤖 ExplainAgent: Received request to explain code.")
        
        # --- System prompt from our notebook ---
        system_prompt = f"""
        You are a CoderLang Explanation Agent, a friendly coding tutor.
        Your sole purpose is to explain the provided code in a simple,
        clear, and concise way.
        
        Do not just describe the code line-by-line. Explain
        what the code *does* and *how it works* at a high level.
        
        ---
        Code:
        {code_string}
        ---
        """
        
        try:
            response = self.model.generate_content(system_prompt)
            explanation = response.text
            print("🤖 ExplainAgent: Explanation successful.")
            return explanation
        except Exception as e:
            print(f"🤖 ExplainAgent: ❌ Explanation failed!")
            print(f"Error: {e}")
            return f"An error occurred: {e}"