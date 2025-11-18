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

# Get a logger for this module
log = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self):
        """
        Initializes the Orchestrator, its planning model, and all available agents.
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
        based on the user's prompt.
        """
        log.info(f"Generating plan for: '{user_prompt}'")
        
        agent_names = list(self.agents.keys())
        
        # This is our strict "meta-prompt"
        system_prompt = f"""
        You are the "brain" of a multi-agent system.
        Your job is to create a step-by-step JSON plan to fulfill a user's request.
        
        You have the following agents available:
        {agent_names}
        
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
            For example, if the user says "write, test, and explain", your plan MUST
            include "CodingAgent", "TestGeneratorAgent", and "ExplainAgent".
        2.  The *first* step must *always* be the 'CodingAgent'. Its 'prompt' argument
            should be your best interpretation of the user's *entire* coding request.
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
        previous_step_output = None 
        
        for i, step in enumerate(plan):
            agent_name = step["agent"]
            args = step["args"]
            
            log.info(f"--- Executing Step {i+1}: {agent_name} ---")
            
            if agent_name not in self.agents:
                log.error(f"Agent '{agent_name}' not found.")
                continue
            
            agent = self.agents[agent_name]
            
            args_copy = args.copy() 
            
            for key, value in args_copy.items():
                if value == "{previous_step_output}":  # <--- THIS IS THE FIX
                    if i == 0:
                        log.error("First step cannot use 'previous_step_output'.")
                        return None
                    
                    if "step_1_CodingAgent" in results:
                        args_copy[key] = results["step_1_CodingAgent"]
                    else:
                        log.error("Could not find 'step_1_CodingAgent' output to pass.")
                        args_copy[key] = None 
            
            try:
                output = agent.run(**args_copy)
                previous_step_output = output 
                results[f"step_{i+1}_{agent_name}"] = output
                
                # --- THIS IS THE NEW, YAML-STYLE LOGGING ---
                log.info(f"Step {i+1} ({agent_name}) execution complete.")

                # We parse and format the output for key agents
                if agent_name == "SafetyAgent":
                    try:
                        # Parse "Verdict: SAFE\nJustification: ..."
                        verdict = output.split('\n')[0].split(':', 1)[1].strip()
                        justification = output.split('\n')[1].split(':', 1)[1].strip()
                        # Log it in the clean YAML style
                        log.info(f"\n  SafetyAgent Verdict: {verdict}\n  Reason: {justification}")
                    except Exception:
                        # --- THIS IS THE FIX ---
                        snippet_no_newlines = output.replace('\n', ' ')
                        log.info(f"  > Output (Snippet): {snippet_no_newlines}")
                        # -----------------------
                
                # For other agents, log a snippet.
                else:
                    snippet = (output.replace('\n', ' ')[:150] + '...')
                    log.info(f"  > Output (Snippet): {snippet}")
                # ----------------------------------------
                
            except Exception as e:
                log.error(f"Error during agent execution: {e}")
                results[f"step_{i+1}_{agent_name}"] = f"ERROR: {e}"
                break 
                
        # --- Final Evaluation Step (Hard-coded) ---
        log.info("--- Executing Step: Evaluator ---")
        if "step_1_CodingAgent" in results:
            code_to_evaluate = results["step_1_CodingAgent"]
            evaluation = evaluate_code(original_prompt, code_to_evaluate)
            results["final_evaluation"] = evaluation
            
            # --- APPLY THE SAME LOGIC HERE ---
            try:
                # Parse "Score: 10/10\nJustification: ..."
                score = evaluation.split('\n')[0].split(':', 1)[1].strip()
                justification = evaluation.split('\n')[1].split(':', 1)[1].strip()
                log.info(f"\n  Score: {score}\n  Justification: {justification}")
            except Exception:
                # --- THIS IS THE FIX ---
                eval_no_newlines = evaluation.replace('\n', ' ')
                log.info(f"  > Evaluation: {eval_no_newlines}")
                # -----------------------
        
        log.info("Plan execution complete.")
        return results