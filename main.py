from dotenv import load_dotenv
load_dotenv()

from orchestrator.router import run_main_flow
import sys
import os
from rich.pretty import pprint

def main():
    """
    Main entry point for the CoderLang application.
    """
    if not os.environ.get("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY not set. Please create a .env file.")
        sys.exit(1)

    prompt = "Write a 'hello world' function in Python."
    
    print("--- CoderLang Application Start ---")
    
    final_result = run_main_flow(prompt)
    
    print("\n--- CoderLang Application End ---")
    print("\nFinal Result:")
    pprint(final_result)

if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

    main()