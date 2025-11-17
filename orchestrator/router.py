import logging
from orchestrator.coordinator import Orchestrator # --- IMPORT FROM COORDINATOR ---

log = logging.getLogger(__name__)

# This function is the main entry point for main.py
def run_orchestrator(user_prompt: str):
    """
    Initializes and runs the main CoderLang orchestrator.
    """
    log.info("Router received request. Initializing Orchestrator...")
    try:
        orchestrator = Orchestrator()
        plan = orchestrator.generate_plan(user_prompt)
        
        if plan:
            final_results = orchestrator.execute_plan(plan, user_prompt)
            return final_results
        else:
            log.warning("Orchestrator could not generate a valid plan.")
            return {"error": "Could not generate a valid plan."}
            
    except Exception as e:
        log.critical(f"A critical error occurred in the orchestrator: {e}")
        return {"error": str(e)}