from dotenv import load_dotenv
load_dotenv()

import logging
import sys
# We don't need the json import anymore
# import json 

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)-8s - %(name)-25s - %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout
)

from orchestrator.router import run_orchestrator
import os

log = logging.getLogger(__name__)

def main():
    """
    Main entry point for the CoderLang application.
    """
    if not os.environ.get("GOOGLE_API_KEY"):
        log.critical("Error: GOOGLE_API_KEY not set. Please create a .env file.")
        sys.exit(1)

    prompt = "Write a Python function to find prime numbers, then explain it, and finally generate tests for it."
    
    log.info(f"--- CoderLang Application Start (Prompt: '{prompt}') ---")
    
    # We can still store the results in a variable,
    # but we don't need to print it.
    final_results = run_orchestrator(prompt)
    
    log.info("--- CoderLang Application End ---")
    
    # --- THIS IS THE FIX ---
    # We no longer "dump" the giant JSON. The step-by-step
    # logs from the orchestrator are our new output.
    print("\nFinal results are available in the logs above.")
    # -----------------------

if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    main()