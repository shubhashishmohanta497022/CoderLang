from google import genai
from google.genai import types
import os
import logging
from config import MODEL_NAME

log = logging.getLogger(__name__)

class ResearchAgent:
    def __init__(self):
        log.info("Initializing Research Agent (New SDK)...")
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found.")
        
        # Initialize the new Client
        self.client = genai.Client(api_key=api_key)
        
        # Define the tool using the new types
        self.google_search_tool = types.Tool(
            google_search=types.GoogleSearch()
        )
        
        self.model_name = MODEL_NAME

    def run(self, query: str, **kwargs) -> str:
        log.info(f"Received research query: {query}")
        
        system_instructions = "You are a CoderLang Research Agent. Search Google and summarize results."
        
        try:
            # The new generate_content syntax
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=f"{system_instructions}\n\nQuery: {query}",
                config=types.GenerateContentConfig(
                    tools=[self.google_search_tool],
                    response_modalities=["TEXT"]
                )
            )
            
            return response.text

        except Exception as e:
            log.error(f"Research failed! Error: {e}")
            return f"An error occurred during research: {e}"