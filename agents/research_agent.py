import google.generativeai as genai
import os
import logging

log = logging.getLogger(__name__)

class ResearchAgent:
    def __init__(self):
        """
        Initializes the Research Agent with Google Search capabilities.
        """
        log.info("Initializing...")
        
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            log.error("GOOGLE_API_KEY not found.")
            raise ValueError("GOOGLE_API_KEY not found.")
        
        genai.configure(api_key=api_key)
        
        # --- THE FIX ---
        # We use 'google_search_retrieval' which is the explicit key 
        # for the Search Grounding tool in the Python SDK.
        # We also set a dynamic threshold (0.6) so it only searches 
        # when the model thinks it's necessary.
        tools_config = [
            {
                "google_search_retrieval": {
                    "dynamic_retrieval_config": {
                        "mode": "dynamic",
                        "dynamic_threshold": 0.6,
                    }
                }
            }
        ]
        
        self.model = genai.GenerativeModel(
            model_name='gemini-2.5-pro',
            tools=tools_config,
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
        )
        log.info("Model configured with Google Search Grounding.")
        
    def run(self, query: str) -> str:
        log.info(f"Received research query: {query}")
        
        system_instructions = """
        You are a CoderLang Research Agent.
        Your sole purpose is to use Google Search to find information about code libraries, errors, or documentation.
        
        You MUST perform a search for the user's query.
        Summarize the search results into a concise, helpful answer for a developer.
        Focus on:
        - API syntax and usage
        - Common solutions to errors
        - Recent changes or deprecations
        """
        
        try:
            # We simply prompt the model. The tool config we added in __init__
            # will automatically trigger the search if the model decides it's needed.
            full_prompt = f"{system_instructions}\n\nUser Query: {query}"
            
            response = self.model.generate_content(full_prompt)
            
            # Extract the text
            result = response.text
            
            # Check for grounding metadata to confirm search happened
            # (This structure can vary slightly by version, so we check safely)
            if hasattr(response.candidates[0], 'grounding_metadata'):
                meta = response.candidates[0].grounding_metadata
                if hasattr(meta, 'search_entry_point') and meta.search_entry_point:
                    log.info("Google Search was successfully performed (Grounding Metadata found).")
            
            log.info("Research successful.")
            return result
        except Exception as e:
            log.error(f"Research failed! Error: {e}")
            return f"An error occurred during research: {e}"