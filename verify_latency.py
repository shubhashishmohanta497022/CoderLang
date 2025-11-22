import asyncio
import time
import os
import logging
import json
from orchestrator.router import run_orchestrator
from dotenv import load_dotenv

load_dotenv()

# Configure logging to see the parallel execution
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

PROMPT = "Research the 'Dining Philosophers Problem' and how to solve it using Python's threading module to prevent deadlocks. Write a complete, deadlock-free solution in Python. Translate the core locking logic to C++. Explain how the concurrency works, add docstrings to all functions, and generate unit tests to verify that all philosophers get to eat."

def main():
    print(f"Starting verification script with prompt: {PROMPT[:50]}...")
    start_time = time.time()
    
    # Run the orchestrator
    result = run_orchestrator(PROMPT)
    
    end_time = time.time()
    duration = end_time - start_time
    
    output = []
    output.append("="*50)
    output.append(f"Total Duration: {duration:.2f} seconds")
    output.append("="*50)
    
    if isinstance(result, dict) and "summary" in result:
        output.append(f"Latency reported by Orchestrator: {result['summary'].get('latency')}")
        output.append(f"Intent: {result['summary'].get('intent')}")
        output.append(f"Generated Code Length: {len(result['summary'].get('generated_code', ''))}")
        output.append(f"Explanation Present: {bool(result['summary'].get('explanation'))}")
        output.append(f"Tests Present: {bool(result['summary'].get('tests'))}")
        output.append(f"Translation Present: {bool(result['summary'].get('translation'))}")
        output.append(f"Safety Present: {bool(result['summary'].get('safety'))}")
        output.append(f"Evaluation Present: {bool(result['summary'].get('evaluation'))}")
        
        output.append("\nRaw Result Keys:")
        output.append(json.dumps(list(result.get("raw_results", {}).keys()), indent=2))
        
        if "CodeGenAgent" in result.get("raw_results", {}):
            output.append("\nCodeGen Result:")
            output.append(json.dumps(result["raw_results"]["CodeGenAgent"], indent=2))
    else:
        output.append("Result format unexpected or error occurred.")
        output.append(str(result))
        
    with open("verification_result.txt", "w") as f:
        f.write("\n".join(output))
        
    print("Verification complete. Results written to verification_result.txt")

if __name__ == "__main__":
    main()
