import asyncio
import concurrent.futures
import hashlib
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

# Import Google GenAI and Dotenv
import google.generativeai as genai
from dotenv import load_dotenv

# Import specific agents if they exist, otherwise we simulate them
from agents.research_agent import ResearchAgent

load_dotenv()

log = logging.getLogger("orchestrator_universal")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

CACHE_DIR = "/tmp/coderlang_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# ========== Config ==========
MODEL_FAST = "gemini-2.0-flash"       # Speed (Router, Chat, Tests, Docs)
MODEL_HEAVY = "gemini-2.0-flash"      # Intelligence (Coding, Complex Debugging) - Switched to Flash due to Pro quota limits during testing

SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# ========== Universal System Prompts ==========
SYSTEM_PROMPTS = {
    # --- THE BRAIN ---
    "TaskRouter": """
    You are the Master Router. Analyze the user request and output a JSON object deciding which agents to activate.
    
    Available Agents:
    - "ResearchAgent": Use if the user asks for facts, web info, or unknown concepts.
    - "GeneralAgent": Use for "Hi", casual chat, or non-technical questions.
    - "CodeGenAgent": Use if the user asks to write, fix, or show code.
    - "SafetyAgent": MANDATORY if "CodeGenAgent" is active. Checks for malicious code.
    - "TestGenAgent": Use if user asks for tests OR for critical code verification.
    - "DocstringAgent": Use if user asks for docs or "production ready" code.
    - "TranslateAgent": Use ONLY if the user explicitly asks to translate code to another language.
    - "ExplainAgent": Use if the user asks for an explanation or if the topic is complex.
    - "EvaluatorAgent": Use if "CodeGenAgent" is active to score the solution.

    OUTPUT JSON ONLY:
    {
        "intent_summary": "short description",
        "agents_to_run": ["Agent1", "Agent2", ...],
        "parallelizable": true
    }
    """,

    # --- STAGE 1: CREATORS ---
    "GeneralAgent": "You are a helpful coding assistant. Answer the user's question continuously and concisely.",
    "ResearchAgent": "Summarize key technical concepts and implementation details for the request.",
    "CodeGenAgent": "You are an Expert Python Architect. Write robust, runnable solution code. Return ONLY code.",

    # --- STAGE 2: DERIVATIVES ---
    "SafetyAgent": "Check the code for unsafe operations (exec, eval, infinite loops). Return Verdict: SAFE/UNSAFE.",
    "TestGenAgent": "Write `unittest` cases for the provided code. Return ONLY the test code.",
    "DocstringAgent": "Add PEP 257 docstrings to the provided code. Return the FULL updated code.",
    "TranslateAgent": "Translate the provided code to the language requested by the user. If not specified, assume C++.",
    "ExplainAgent": "Explain the solution's logic and architecture concisely.",

    # --- STAGE 3: JUDGE ---
    "EvaluatorAgent": "Evaluate the solution (Code, Tests, Docs). Score 1-10. Format: 'Score: X/10. Justification: ...'"
}

# ========== Orchestrator ==========

class OrchestratorSession:
    """
    Represents a single resumable execution session.
    State is serializable to JSON for LocalStorage persistence.
    """
    def __init__(self, orchestrator, prompt: str, state: Optional[Dict] = None):
        self.orch = orchestrator
        self.prompt = prompt
        
        if state:
            self.state = state
        else:
            self.state = {
                "stage": "INIT",  # INIT -> PLANNED -> STAGE1 -> STAGE2 -> STAGE3 -> COMPLETE
                "plan": {},
                "results": {},
                "start_time": time.time(),
                "logs": []
            }

    def log(self, message: str):
        entry = f"{time.strftime('%H:%M:%S')} - {message}"
        self.state["logs"].append(entry)
        logging.info(f"[{self.state['stage']}] {message}")

    def to_json(self) -> Dict:
        return {
            "prompt": self.prompt,
            "state": self.state
        }

    async def run_next_step(self):
        """Advances the workflow by one stage."""
        stage = self.state["stage"]
        results = self.state["results"]
        
        # --- STAGE 0: ROUTING ---
        if stage == "INIT":
            self.log("🧠 Routing Request...")
            route_res = await self.orch.run_llm("Router", MODEL_FAST, SYSTEM_PROMPTS["TaskRouter"], self.prompt)
            try:
                plan = json.loads(route_res["text"])
                # Normalize keys
                if "agents_to_run" not in plan: plan["agents_to_run"] = ["GeneralAgent"]
                if "parallelizable" not in plan: plan["parallelizable"] = False
            except:
                self.log("⚠️ Router failed JSON parse. Defaulting to GeneralChat.")
                plan = {"intent_summary": "Fallback", "agents_to_run": ["GeneralAgent"], "parallelizable": False}
            
            self.state["plan"] = plan
            self.state["stage"] = "PLANNED"
            self.log(f"📋 Plan: {plan['agents_to_run']}")
            return

        active_agents = self.state["plan"].get("agents_to_run", [])

        # --- STAGE 1: CREATION ---
        if stage == "PLANNED":
            self.log("🚀 Starting Stage 1 (Creation)...")
            tasks = []
            
            if "ResearchAgent" in active_agents:
                tasks.append(("ResearchAgent", self.orch.run_llm("Research", MODEL_FAST, SYSTEM_PROMPTS["ResearchAgent"], self.prompt)))
            
            if "GeneralAgent" in active_agents and "CodeGenAgent" not in active_agents:
                tasks.append(("GeneralAgent", self.orch.run_llm("Chat", MODEL_FAST, SYSTEM_PROMPTS["GeneralAgent"], self.prompt)))
                
            if "CodeGenAgent" in active_agents:
                tasks.append(("CodeGenAgent", self.orch.run_llm("CodeGen", MODEL_HEAVY, SYSTEM_PROMPTS["CodeGenAgent"], self.prompt, max_tokens=4000)))
                
            if "ExplainAgent" in active_agents:
                tasks.append(("ExplainAgent", self.orch.run_llm("Explain", MODEL_FAST, SYSTEM_PROMPTS["ExplainAgent"], self.prompt)))

            if tasks:
                names = [t[0] for t in tasks]
                coros = [t[1] for t in tasks]
                results_s1 = await asyncio.gather(*coros)
                for name, res in zip(names, results_s1):
                    results[name] = res
            
            self.state["stage"] = "STAGE1"
            self.log("✅ Stage 1 Complete.")
            return

        # --- STAGE 2: DERIVATIVES ---
        if stage == "STAGE1":
            base_code = results.get("CodeGenAgent", {}).get("text", "")
            if not base_code:
                self.log("⏩ No code generated, skipping Stage 2.")
                self.state["stage"] = "STAGE2"
                return

            self.log("⚡ Starting Stage 2 (Derivatives)...")
            context_for_derivs = f"Original Request: {self.prompt}\n\nCode:\n{base_code}"
            tasks = []

            def make_task(agent_name, model=MODEL_FAST):
                return (agent_name, self.orch.run_llm(agent_name, model, SYSTEM_PROMPTS[agent_name], context_for_derivs))

            if "SafetyAgent" in active_agents: tasks.append(make_task("SafetyAgent"))
            if "TestGenAgent" in active_agents: tasks.append(make_task("TestGenAgent"))
            if "DocstringAgent" in active_agents: tasks.append(make_task("DocstringAgent"))
            if "TranslateAgent" in active_agents: tasks.append(make_task("TranslateAgent"))

            if tasks:
                names = [t[0] for t in tasks]
                coros = [t[1] for t in tasks]
                results_s2 = await asyncio.gather(*coros)
                for name, res in zip(names, results_s2):
                    results[name] = res

            # Update base code if docstrings were added
            if results.get("DocstringAgent", {}).get("ok"):
                # We store the docstring version as the 'final' code in a separate key or just overwrite
                # For simplicity, let's overwrite the display code in summary later, but keep raw result here
                pass

            self.state["stage"] = "STAGE2"
            self.log("✅ Stage 2 Complete.")
            return

        # --- STAGE 3: EVALUATION ---
        if stage == "STAGE2":
            base_code = results.get("DocstringAgent", {}).get("text") or results.get("CodeGenAgent", {}).get("text", "")
            
            if "EvaluatorAgent" in active_agents and base_code:
                self.log("⚖️ Starting Stage 3 (Evaluation)...")
                eval_ctx = f"Req: {self.prompt}\nCode: {base_code}\nTests: {results.get('TestGenAgent', {}).get('text','')}"
                results["EvaluatorAgent"] = await self.orch.run_llm("Evaluator", MODEL_FAST, SYSTEM_PROMPTS["EvaluatorAgent"], eval_ctx)
            
            self.state["stage"] = "COMPLETE"
            self.log("✅ Workflow Complete.")
            return

    def get_summary(self) -> Dict:
        """Generates the summary object expected by the UI."""
        results = self.state["results"]
        plan = self.state["plan"]
        
        # Determine final code (Docstring > CodeGen)
        base_code = results.get("DocstringAgent", {}).get("text") or results.get("CodeGenAgent", {}).get("text", "")
        
        latency = time.time() - self.state["start_time"]
        
        return {
            "intent": plan.get("intent_summary", "Task"),
            "generated_code": base_code,
            "explanation": results.get("ExplainAgent", {}).get("text") or results.get("GeneralAgent", {}).get("text"),
            "tests": results.get("TestGenAgent", {}).get("text"),
            "translation": results.get("TranslateAgent", {}).get("text"),
            "safety": results.get("SafetyAgent", {}).get("text"),
            "evaluation": results.get("EvaluatorAgent", {}).get("text"),
            "latency": f"{latency:.2f}s",
            "stage": self.state["stage"],
            "logs": self.state["logs"]
        }


class Orchestrator:
    def __init__(self, max_workers: int = 10):
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    async def run_llm(self, task_name: str, model: str, system_prompt: str, input_context: str, max_tokens: int = 2000) -> Dict:
        """Universal Async LLM Caller"""
        api_key = os.environ.get("GOOGLE_API_KEY")
        genai.configure(api_key=api_key)

        def _blocking_call():
            m = genai.GenerativeModel(model_name=model, safety_settings=SAFETY_SETTINGS)
            full_prompt = f"{system_prompt}\n\n[Context]:\n{input_context}"
            try:
                res = m.generate_content(full_prompt)
                text = res.text
                if "```" in text: 
                    text = text.replace("```json", "").replace("```python", "").replace("```", "").strip()
                return {"text": text, "ok": True}
            except Exception as e:
                return {"text": "", "error": str(e), "ok": False}

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.executor, _blocking_call)

    def create_session(self, prompt: str, state: Optional[Dict] = None) -> OrchestratorSession:
        return OrchestratorSession(self, prompt, state)

    # Legacy wrapper for backward compatibility if needed
    async def run_plan(self, user_prompt: str) -> Dict[str, Any]:
        session = self.create_session(user_prompt)
        while session.state["stage"] != "COMPLETE":
            await session.run_next_step()
        
        return {
            "summary": session.get_summary(),
            "raw_results": session.state["results"]
        }