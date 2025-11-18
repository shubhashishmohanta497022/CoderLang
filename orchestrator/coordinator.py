import google.generativeai as genai
import os
import json
import logging

# Import all our agents
from agents.coding_agent import CodingAgent
from agents.safety_agent import SafetyAgent
from agents.translate_agent import TranslateAgent
from agents.test_generator_agent import TestGeneratorAgent
from agents.explain_agent import ExplainAgent
from agents.debugging_agent import DebuggingAgent
from agents.doc_agent import DocumentationAgent
from orchestrator.evaluator import evaluate_code

# Import Tools
from tools.run_code import run_python_code
from memory.memory_store import MemoryStore

# Get a logger for this module
log = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self):
        """
        Initializes the Orchestrator, its planning model, memory, and all available agents.
        """
        log.info("Initializing...")
        
        # Configure the planning model
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            log.error("GOOGLE_API_KEY not found.")
            raise ValueError("GOOGLE_API_KEY not found.")
        
        genai.configure(api_key=api_key)
        
        self.planner_model = genai.GenerativeModel(
            model_name='gemini-2.5-pro',
            safety_settings=[{"category": c, "threshold": "BLOCK_NONE"} for c in [
                "HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"
            ]]
        )
        log.info("Planner model configured.")

        # Initialize Memory
        self.memory = MemoryStore()
        log.info("MemoryStore initialized.")

        # Create a "toolbox" of all our agents
        self.agents = {
            "CodingAgent": CodingAgent(),
            "SafetyAgent": SafetyAgent(),
            "TranslateAgent": TranslateAgent(),
            "TestGeneratorAgent": TestGeneratorAgent(),
            "ExplainAgent": ExplainAgent(),
            "DebuggingAgent": DebuggingAgent(),
            "DocumentationAgent": DocumentationAgent(),
        }
        log.info(f"Loaded {len(self.agents)} agents into toolbox.")

    def generate_plan(self, user_prompt: str):
        """
        Calls the LLM to generate a structured plan (JSON)
        based on the user's prompt and memory context.
        """
        log.info(f"Generating plan for: '{user_prompt}'")
        
        # Fetch Memory Context
        memory_context = self.memory.get_all_context()
        if memory_context:
            log.info(f"Injected Memory Context:\n{memory_context.strip()}")
        
        agent_names = list(self.agents.keys())
        
        # This is our strict "meta-prompt"
        system_prompt = f"""
        You are the "brain" of a multi-agent system.
        Your job is to create a step-by-step JSON plan to fulfill a user's request.
        
        You have the following agents available:
        {agent_names}
        
        --- MEMORY CONTEXT (User Preferences) ---
        {memory_context}
        -----------------------------------------
        
        Your plan MUST be a JSON list of steps.
        Each step must be a dictionary with an "agent" key and an "args" key.
        
        Here are the argument signatures:
        - CodingAgent(prompt: str)
        - SafetyAgent(code_string: str)
        - TranslateAgent(code_string: str, target_language: str)
        - TestGeneratorAgent(code_string: str)
        - ExplainAgent(code_string: str)
        - DebuggingAgent(code_string: str, error_message: str)
        - DocumentationAgent(code_string: str)
        
        RULES:
        1.  You MUST create a step for *every* distinct action in the user's request.
        2.  The *first* step must *always* be the 'CodingAgent'. Its 'prompt' argument
            should be your best interpretation of the user's *entire* coding request,
            incorporating any preferences from the Memory Context.
        3.  The *second* step must *always* be the 'SafetyAgent' to check the code.
        4.  For all steps after 'CodingAgent', you MUST use the placeholder string
            "{{previous_step_output}}" as the 'code_string' argument.
        5.  Do not add agents that the user did not ask for, *except* for the
            mandatory 'CodingAgent' and 'SafetyAgent'.
            
        The user's request is: "{user_prompt}"
        
        Now, generate the JSON plan for the user's request.
        Provide *only* the raw JSON list. No markdown, no explanations.
        """
        
        try:
            response = self.planner_model.generate_content(system_prompt)
            plan_json = response.text.strip().replace("```json", "").replace("```", "").strip()
            
            log.info(f"Plan generated:\n{plan_json}")
            return json.loads(plan_json)
        
        except Exception as e:
            raw_response = response.text if 'response' in locals() else 'No response from model'
            log.error(f"FAILED to generate or parse plan! Error: {e}\nRaw Response: {raw_response}")
            return None

    def execute_plan(self, plan: list, original_prompt: str):
        """
        Executes the generated plan step-by-step.
        """
        log.info("Starting plan execution...")
        
        results = {}
        original_code = None 
        
        for i, step in enumerate(plan):
            agent_name = step["agent"]
            args = step["args"]
            
            log.info(f"--- Executing Step {i+1}: {agent_name} ---")
            
            if agent_name not in self.agents:
                log.error(f"Agent '{agent_name}' not found.")
                continue
            
            agent = self.agents[agent_name]
            
            args_copy = args.copy() 
            
            # Robust Placeholder Replacement
            for key, value in args_copy.items():
                if isinstance(value, str) and "previous_step_output" in value:
                    if original_code:
                        args_copy[key] = original_code 
                    else:
                        log.error("Placeholder found but no 'original_code' available to pass.")
                        # Fallback to recover if possible
                        if "step_1_CodingAgent" in results:
                             args_copy[key] = results["step_1_CodingAgent"]
                             original_code = results["step_1_CodingAgent"] 
                        else:
                             args_copy[key] = None
            
            try:
                output = agent.run(**args_copy)
                
                # If this is the CodingAgent, capture the code immediately
                if agent_name == "CodingAgent":
                    original_code = output
                
                results[f"step_{i+1}_{agent_name}"] = output
                
                log.info(f"Step {i+1} ({agent_name}) execution complete.")

                # Logging Logic
                if agent_name == "SafetyAgent":
                    try:
                        verdict = output.split('\n')[0].split(':', 1)[1].strip()
                        justification = output.split('\n')[1].split(':', 1)[1].strip()
                        log.info(f"\n  SafetyAgent Verdict: {verdict}\n  Reason: {justification}")
                    except Exception:
                        snippet_no_newlines = output.replace('\n', ' ')
                        log.info(f"  > Output (Snippet): {snippet_no_newlines}")
                else:
                    snippet = (output.replace('\n', ' ')[:150] + '...')
                    log.info(f"  > Output (Snippet): {snippet}")
                
                
                # --- DYNAMIC TEST & DEBUG LOOP ---
                if agent_name == "TestGeneratorAgent" and original_code:
                    log.info("--- Executing Step: Run Tests (Auto) ---")
                    test_code = output 
                    
                    combined_code = original_code + "\n\n" + test_code
                    
                    test_results = run_python_code(combined_code)
                    results["step_auto_RunTests"] = test_results
                    
                    if test_results["stderr"]:
                        log.warning(f"Test run FAILED:\n{test_results['stderr']}")
                        
                        log.info("--- Executing Step: Debug (Auto) ---")
                        debug_agent = self.agents.get("DebuggingAgent")
                        
                        if debug_agent:
                            try:
                                fixed_code = debug_agent.run(
                                    code_string=original_code, 
                                    error_message=test_results["stderr"]
                                )
                                log.info("Auto-debug attempt complete.")
                                
                                # Update original_code with the FIX
                                original_code = fixed_code 
                                results["step_auto_Debug"] = fixed_code
                                log.info("  > (Auto-Debug) Output (Snippet): " + (fixed_code.replace('\n', ' ')[:150] + '...'))
                                
                                # Re-Run Tests
                                log.info("--- Executing Step: Re-Run Tests (Auto) ---")
                                new_combined_code = original_code + "\n\n" + test_code
                                retest_results = run_python_code(new_combined_code)
                                results["step_auto_ReRunTests"] = retest_results
                                
                                if retest_results["stderr"]:
                                    log.warning(f"RE-TEST FAILED:\n{retest_results['stderr']}")
                                else:
                                    log.info(f"RE-TEST PASSED! STDOUT: {retest_results['stdout']}")
                                    
                            except Exception as e:
                                log.error(f"Auto-debug step failed: {e}")
                        else:
                            log.warning("Test failed, but DebuggingAgent not found.")
                    
                    else: # No stderr
                        log.info("Test run PASSED!")
                        log.info(f"  > STDOUT: {test_results['stdout']}")
                # --- END DYNAMIC LOOP ---
                
            except Exception as e:
                log.error(f"Error during agent execution: {e}")
                results[f"step_{i+1}_{agent_name}"] = f"ERROR: {e}"
                break 
                
        # --- Final Evaluation Step ---
        log.info("--- Executing Step: Evaluator ---")
        if original_code: 
            code_to_evaluate = original_code
            evaluation = evaluate_code(original_prompt, code_to_evaluate)
            results["final_evaluation"] = evaluation
            
            try:
                score = evaluation.split('\n')[0].split(':', 1)[1].strip()
                justification = evaluation.split('\n')[1].split(':', 1)[1].strip()
                log.info(f"\n  Score: {score}\n  Justification: {justification}")
            except Exception:
                eval_no_newlines = evaluation.replace('\n', ' ')
                log.info(f"  > Evaluation: {eval_no_newlines}")
        
        log.info("Plan execution complete.")
        return results