import logging
import asyncio
import sys

# Try to import nest_asyncio for Streamlit/Jupyter compatibility
try:
    import nest_asyncio
except ImportError:
    nest_asyncio = None

from orchestrator.coordinator import Orchestrator

log = logging.getLogger(__name__)

def run_orchestrator(user_prompt: str):
    """
    Synchronous Entry Point for the Async Orchestrator.
    This function is called by main.py and app.py.
    """
    log.info(f"Router received: {user_prompt[:50]}...")
    
    try:
        orchestrator = Orchestrator()
        
        # 1. Check for an existing event loop (common in Streamlit/Jupyter)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # We are in an existing loop (Streamlit)
            if nest_asyncio:
                # Patch the loop to allow nested execution
                nest_asyncio.apply()
                return loop.run_until_complete(orchestrator.run_plan(user_prompt))
            else:
                log.warning("⚠️ nest_asyncio not found! Streamlit execution might fail.")
                # Attempt execution anyway (might work in some Python versions)
                return loop.run_until_complete(orchestrator.run_plan(user_prompt))
        else:
            # We are in a standard script (CLI / main.py)
            return asyncio.run(orchestrator.run_plan(user_prompt))

    except Exception as e:
        log.critical(f"Orchestrator Bridge Failed: {e}")
        # Return a safe error dictionary compatible with the frontend
        return {
            "summary": {
                "intent": "Error",
                "generated_code": "",
                "explanation": f"System Error: {str(e)}",
                "error": str(e)
            },
            "raw_results": {}
        }