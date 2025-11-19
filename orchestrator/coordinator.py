import google.generativeai as genai
import os
import json
import logging
import concurrent.futures
from config import FAST_MODEL, SMART_MODEL, SAFETY_SETTINGS

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

log = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self):
        log.info("Initializing Orchestrator...")
        
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            log.error("GOOGLE_API_KEY not found.")
            raise ValueError("GOOGLE_API_KEY not found.")
        
        genai.configure(api_key=api_key)
        
        # Default to FAST model for Planning/Routing
        self.planner_model = genai.GenerativeModel(
            model_name=FAST_MODEL,
            safety_settings=SAFETY_SETTINGS
        )
        log.info(f"Planner/Router initialized using {FAST_MODEL}.")

        self.memory = MemoryStore()
        
        # Initialize all agents (Defaulting to whatever config.MODEL_NAME was, usually Flash)
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
        self.file_tool = FileTool()

    def _optimize_agent_models(self, complexity: str):
        """
        Dynamically swaps agent brains based on task complexity.
        """
        if complexity == "COMPLEX":
            log.info(f"🧠 SWITCHING TO SMART MODE ({SMART_MODEL}) for Coding/Debugging.")
            # We hot-swap the model object inside the specific agents
            smart_model_obj = genai.GenerativeModel(model_name=SMART_MODEL, safety_settings=SAFETY_SETTINGS)
            
            # Only upgrade the "Brain" agents
            self.agents["CodingAgent"].model = smart_model_obj
            self.agents["DebuggingAgent"].model = smart_model_obj
            self.agents["ExplainAgent"].model = smart_model_obj # Optional: Explain in detail
        else:
            log.info(f"⚡ REMAINING IN FAST MODE ({FAST_MODEL}) for simple task.")

    def generate_plan(self, user_prompt: str):
        log.info(f"Analyzing request: '{user_prompt}'")
        
        # --- 1. ROUTER STEP: Determine Complexity ---
        try:
            router_prompt = f"""
            Analyze this coding request: "{user_prompt}"
            Is this a 'SIMPLE' task (e.g., parsing, basic scripts, fibonacci) 
            or a 'COMPLEX' task (e.g., architecture, advanced algorithms, debugging w/ no context)?
            Respond with ONLY the word SIMPLE or COMPLEX.
            """
            router_response = self.planner_model.generate_content(router_prompt)
            complexity = router_response.text.strip().upper()
            if "COMPLEX" not in complexity: complexity = "SIMPLE"
            
            # Apply the model switch
            self._optimize_agent_models(complexity)
            
        except Exception as e:
            log.warning(f"Router failed, defaulting to simple mode: {e}")
            complexity = "SIMPLE"

        # --- 2. PLANNER STEP ---
        memory_context = self.memory.get_all_context()
        agent_names = list(self.agents.keys())
        
        system_prompt = f"""
        You are the "brain" of a multi-agent system.
        Create a step-by-step JSON plan.
        
        Agents: {agent_names}
        Context: {memory_context}
        Complexity Level: {complexity}
        
        RULES:
        1. Start with 'ResearchAgent' only if asking for specific knowledge.
        2. 'CodingAgent' is MANDATORY for code tasks.
        3. 'SafetyAgent' is MANDATORY after coding.
        4. IF Complexity is 'COMPLEX': ALWAYS include TestGenerator, ExplainAgent, DocumentationAgent.
        5. IF Complexity is 'SIMPLE': You MAY skip Explain/Doc agents to save time, unless explicitly requested.
        6. Use "{{previous_step_output}}" for 'code_string' arguments.

        User Request: "{user_prompt}"
        
        Generate JSON list.
        """
        
        try:
            response = self.planner_model.generate_content(system_prompt)
            plan_json = response.text.strip().replace("```json", "").replace("```", "").strip()
            return json.loads(plan_json)
        except Exception as e:
            log.error(f"FAILED to generate plan! Error: {e}")
            return None

    def execute_plan(self, plan: list, original_prompt: str):
        log.info("Starting plan execution...")
        results = {}
        original_code = None 
        research_context = ""
        executed_indices = set()
        
        for i, step in enumerate(plan):
            if i in executed_indices: continue
            
            agent_name = step["agent"]
            
            # --- PARALLELIZATION LOGIC ---
            independent_agents = ["ExplainAgent", "TestGeneratorAgent", "DocumentationAgent", "TranslateAgent"]
            parallel_candidates = []
            
            if agent_name in independent_agents:
                for j in range(i + 1, len(plan)):
                    other_step = plan[j]
                    if other_step["agent"] in independent_agents and other_step["agent"] != agent_name:
                        parallel_candidates.append((j, other_step))
            
            if parallel_candidates:
                other_idx, other_step = parallel_candidates[0]
                other_agent_name = other_step["agent"]
                
                log.info(f"⚡ OPTIMIZATION: Running {agent_name} and {other_agent_name} in PARALLEL.")
                
                def prepare_args(step_args):
                    a_args = step_args.copy()
                    if "prompt" in a_args and research_context:
                         a_args["prompt"] += f"\n\n[Context]:\n{research_context}"
                    for k, v in a_args.items():
                        if isinstance(v, str) and "previous_step_output" in v:
                            a_args[k] = original_code if original_code else ""
                    if original_code and "code_string" in a_args:
                        a_args["code_string"] = original_code
                    return a_args

                args_1 = prepare_args(step["args"])
                args_2 = prepare_args(other_step["args"])
                
                try:
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future_1 = executor.submit(self.agents[agent_name].run, **args_1)
                        future_2 = executor.submit(self.agents[other_agent_name].run, **args_2)
                        output_1, output_2 = future_1.result(), future_2.result()
                        
                    results[f"step_{i+1}_{agent_name}"] = output_1
                    results[f"step_{other_idx+1}_{other_agent_name}"] = output_2
                    executed_indices.add(i)
                    executed_indices.add(other_idx)
                    
                    for a_name, a_out in [(agent_name, output_1), (other_agent_name, output_2)]:
                        if a_name == "TestGeneratorAgent" and original_code:
                             self._handle_test_execution(original_code, a_out, results)
                    continue
                except Exception as e:
                    log.error(f"Parallel failed: {e}")

            # --- SEQUENTIAL EXECUTION ---
            if agent_name not in self.agents: continue
            
            agent = self.agents[agent_name]
            args_copy = step["args"].copy()
            
            if agent_name == "CodingAgent" and research_context:
                args_copy["prompt"] += f"\n\n[Context]:\n{research_context}"
            
            for k, v in args_copy.items():
                if isinstance(v, str) and "previous_step_output" in v:
                    args_copy[k] = original_code if original_code else ""
            
            if original_code and "code_string" in args_copy:
                args_copy["code_string"] = original_code

            try:
                output = agent.run(**args_copy)
                
                if agent_name == "CodingAgent": original_code = output
                elif agent_name == "ResearchAgent": research_context = output
                
                results[f"step_{i+1}_{agent_name}"] = output
                
                if agent_name == "TestGeneratorAgent" and original_code:
                    self._handle_test_execution(original_code, output, results)
                    
            except Exception as e:
                log.error(f"Agent error: {e}")
                break

        # Evaluation
        if original_code:
            expl = next((v for k,v in results.items() if "Explain" in k), "")
            tests = next((v for k,v in results.items() if "Test" in k), "")
            results["final_evaluation"] = evaluate_code(original_prompt, original_code, expl, tests)

        return results

    def _handle_test_execution(self, original_code, test_code, results):
        combined = original_code + "\n\n" + test_code
        res = run_python_code(combined)
        results["step_auto_RunTests"] = res
        if res["stderr"]:
            log.info("Tests failed, debugging...")
            debug_agent = self.agents.get("DebuggingAgent")
            if debug_agent:
                try:
                    fixed = debug_agent.run(original_code, res["stderr"])
                    results["step_auto_Debug"] = fixed
                except: pass