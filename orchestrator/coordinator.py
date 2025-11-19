import google.generativeai as genai
import os
import json
import logging

# --- Import all Agents ---
from agents.coding_agent import CodingAgent
from agents.safety_agent import SafetyAgent
from agents.translate_agent import TranslateAgent
from agents.test_generator_agent import TestGeneratorAgent
from agents.explain_agent import ExplainAgent
from agents.debugging_agent import DebuggingAgent
from agents.doc_agent import DocumentationAgent
from agents.research_agent import ResearchAgent

# --- Import Tools and Utilities ---
from tools.run_code import run_python_code
from tools.file_tool import FileTool
from memory.memory_store import MemoryStore
from orchestrator.evaluator import evaluate_code

# Get a logger for this module
log = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self):
        """
        Initializes the Orchestrator, its planning model, memory, and all available agents.
        """
        log.info("Initializing Orchestrator...")
        
        # 1. Configure Gemini
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            log.error("GOOGLE_API_KEY not found.")
            raise ValueError("GOOGLE_API_KEY not found.")
        
        genai.configure(api_key=api_key)
        
        # 2. Configure the Planner Model
        self.planner_model = genai.GenerativeModel(
            model_name='gemini-2.5-pro',
            safety_settings=[{"category": c, "threshold": "BLOCK_NONE"} for c in [
                "HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"
            ]]
        )
        log.info("Planner model configured.")

        # 3. Initialize Memory
        self.memory = MemoryStore()
        log.info("MemoryStore initialized.")

        # 4. Initialize the ToolBox of Agents
        self.agents = {
            "CodingAgent": CodingAgent(),
            "SafetyAgent": SafetyAgent(),
            "TranslateAgent": TranslateAgent(),
            "TestGeneratorAgent": TestGeneratorAgent(),
            "ExplainAgent": ExplainAgent(),
            "DebuggingAgent": DebuggingAgent(),
            "DocumentationAgent": DocumentationAgent(),
            "ResearchAgent": ResearchAgent(),
        }
        
        # 5. Initialize Utility Tools
        self.file_tool = FileTool()
        
        log.info(f"Loaded {len(self.agents)} agents into toolbox.")

    def generate_plan(self, user_prompt: str):
        """
        Calls the LLM to generate a structured plan (JSON).
        """
        log.info(f"Generating plan for: '{user_prompt}'")
        
        memory_context = self.memory.get_all_context()
        agent_names = list(self.agents.keys())
        
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
        - ResearchAgent(query: str)
        - SafetyAgent(code_string: str)
        - TranslateAgent(code_string: str, target_language: str)
        - TestGeneratorAgent(code_string: str)
        - ExplainAgent(code_string: str)
        - DebuggingAgent(code_string: str, error_message: str)
        - DocumentationAgent(code_string: str)
        
        RULES:
        1.  Create a step for *every* distinct action needed.
        2.  If the user asks for information, start with 'ResearchAgent'.
        3.  If the user asks to write code, 'CodingAgent' is MANDATORY.
        4.  'SafetyAgent' is MANDATORY immediately after 'CodingAgent'.
        5.  For steps after 'CodingAgent', use "{{previous_step_output}}" as the 'code_string'.
            
        The user's request is: "{user_prompt}"
        
        Generate the JSON plan. No markdown.
        """
        
        try:
            response = self.planner_model.generate_content(system_prompt)
            plan_json = response.text.strip().replace("```json", "").replace("```", "").strip()
            log.info(f"Plan generated:\n{plan_json}")
            return json.loads(plan_json)
        
        except Exception as e:
            log.error(f"FAILED to generate plan! Error: {e}")
            return None

    def execute_plan(self, plan: list, original_prompt: str):
        """
        Executes the generated plan step-by-step.
        """
        log.info("Starting plan execution...")
        
        results = {}
        original_code = None 
        research_context = ""
        
        for i, step in enumerate(plan):
            agent_name = step["agent"]
            args = step["args"]
            
            log.info(f"--- Executing Step {i+1}: {agent_name} ---")
            
            if agent_name not in self.agents:
                log.error(f"Agent '{agent_name}' not found.")
                continue
            
            agent = self.agents[agent_name]
            args_copy = args.copy() 
            
            # --- 1. Inject Research Context ---
            if agent_name == "CodingAgent" and research_context:
                log.info("Injecting research context into CodingAgent prompt...")
                args_copy["prompt"] = args_copy["prompt"] + f"\n\n[Context from Research]:\n{research_context}"

            # --- 2. STANDARD Placeholder Replacement ---
            for key, value in args_copy.items():
                if isinstance(value, str) and "previous_step_output" in value:
                    if original_code:
                        args_copy[key] = original_code 
                    else:
                         # Fallback: try to get it from result history
                        for k, v in results.items():
                             if "CodingAgent" in k and isinstance(v, str):
                                  args_copy[key] = v
                                  original_code = v
                                  break
                        if not original_code:
                             log.warning("Placeholder found but no code available. Passing empty string.")
                             args_copy[key] = ""

            # --- 3. CRITICAL FIX: FORCE CODE INJECTION ---
            # The planner sometimes hallucinates specific text (like "classify triangle") 
            # in the 'code_string' argument instead of using the placeholder. 
            # We must OVERRIDE this if we have generated code and the agent is a downstream consumer.
            if original_code and agent_name in [
                "SafetyAgent", "TranslateAgent", "TestGeneratorAgent", 
                "ExplainAgent", "DebuggingAgent", "DocumentationAgent"
            ]:
                if "code_string" in args_copy:
                    log.info(f"  > Guardrail: Forcing 'original_code' into {agent_name} args.")
                    args_copy["code_string"] = original_code

            
            try:
                # --- RUN THE AGENT ---
                output = agent.run(**args_copy)
                
                # --- CAPTURE OUTPUTS ---
                if agent_name == "CodingAgent":
                    original_code = output
                elif agent_name == "ResearchAgent":
                    research_context = output
                
                results[f"step_{i+1}_{agent_name}"] = output
                
                log.info(f"Step {i+1} ({agent_name}) execution complete.")
                
                snippet = str(output).replace('\n', ' ')[:100] + '...'
                log.info(f"  > Output: {snippet}")
                
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
                                original_code = fixed_code 
                                results["step_auto_Debug"] = fixed_code
                                
                                log.info("--- Executing Step: Re-Run Tests (Auto) ---")
                                new_combined_code = original_code + "\n\n" + test_code
                                retest_results = run_python_code(new_combined_code)
                                results["step_auto_ReRunTests"] = retest_results
                                
                                if retest_results["stderr"]:
                                    log.warning("RE-TEST FAILED even after debugging.")
                                else:
                                    log.info("RE-TEST PASSED!")
                                    
                            except Exception as e:
                                log.error(f"Auto-debug step failed: {e}")
                    else: 
                        log.info("Test run PASSED!")
                
            except Exception as e:
                log.error(f"Error during agent execution: {e}")
                results[f"step_{i+1}_{agent_name}"] = f"ERROR: {e}"
                break 
                
        # --- Final Evaluation Step ---
        log.info("--- Executing Step: Evaluator ---")
        if original_code:
            # Gather all relevant context for the evaluator
            explanation_text = ""
            tests_text = ""
            
            # Iterate through results to find explanation and tests
            for key, val in results.items():
                if "ExplainAgent" in key:
                    explanation_text = val
                elif "TestGeneratorAgent" in key:
                    tests_text = val

            # Use the updated evaluator signature
            evaluation = evaluate_code(
                original_prompt, 
                original_code, 
                explanation=explanation_text, 
                tests=tests_text
            )
            results["final_evaluation"] = evaluation
            
            # Log the full evaluation so we can see the justification
            log.info(f"  > Evaluator Output:\n{evaluation}")
        
        log.info("Plan execution complete.")
        return results