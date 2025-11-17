import google.generativeai as genai
import os
import logging

log = logging.getLogger(__name__)

# Initialize the model once when the module is imported
try:
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        log.error("GOOGLE_API_KEY not found.")
        raise ValueError("GOOGLE_API_KEY not found.")
    
    genai.configure(api_key=api_key)
    
    model = genai.GenerativeModel(
        model_name='gemini-2.5-pro',
        safety_settings=[
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
    )
    log.info("Model configured (gemini-2.5-pro).")

except Exception as e:
    log.critical(f"FAILED TO INITIALIZE MODEL: {e}")
    model = None

def evaluate_code(prompt: str, code_string: str) -> str:
    """
    Runs the Judge/Evaluator agent.
    """
    if model is None:
        log.error("Evaluator model not initialized.")
        return "Evaluator model not initialized."
        
    log.info("Received request to evaluate code.")
    
    system_prompt = f"""
    You are a CoderLang Judge/Evaluator Agent.
    Your sole purpose is to evaluate a piece of code based on a user request.
    
    You must provide two things:
    1. A score from 1 (terrible) to 10 (perfect).
    2. A one-sentence justification for your score.
    
    Format your response as:
    Score: [Your Score]/10
    Justification: [Your Justification]
    
    ---
    User Request:
    {prompt}
    ---
    Generated Code:
    {code_string}
    ---
    """
    
    try:
        response = model.generate_content(system_prompt)
        evaluation = response.text.strip()
        log.info("Evaluation successful.")
        return evaluation
    except Exception as e:
        log.error(f"Evaluation failed! Error: {e}")
        return f"An error occurred: {e}"