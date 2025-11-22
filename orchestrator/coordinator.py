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
class Orchestrator:
    def __init__(self, max_workers: int = 10):
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.research_agent = None # Lazy load

    async def run_llm(self, task_name: str, model: str, system_prompt: str, input_context: str, max_tokens: int = 2000) -> Dict:
        """Universal Async LLM Caller"""
        api_key = os.environ.get("GOOGLE_API_KEY")
        genai.configure(api_key=api_key)

        def _blocking_call():
            # Fallback to 1.5 Pro if 2.0 Pro Exp is not available or fails (handled by try/except below roughly)
            # But for now we trust the config.
            m = genai.GenerativeModel(model_name=model, safety_settings=SAFETY_SETTINGS)
            full_prompt = f"{system_prompt}\n\n[Context]:\n{input_context}"
            try:
                res = m.generate_content(full_prompt)
                text = res.text
                # Basic markdown stripper
                if "```" in text: 
                    text = text.replace("```json", "").replace("```python", "").replace("```", "").strip()
                return {"text": text, "ok": True}
            except Exception as e:
                return {"text": "", "error": str(e), "ok": False}

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.executor, _blocking_call)

    async def run_plan(self, user_prompt: str) -> Dict[str, Any]:
        results = {}
        start_time = time.time()
        log.info(f"▶️ Request: {user_prompt[:50]}...")

        # =========================================================================
        # 🧠 PHASE 0: ROUTING (The Brain)
        # =========================================================================
        route_res = await self.run_llm("Router", MODEL_FAST, SYSTEM_PROMPTS["TaskRouter"], user_prompt)
        try:
            plan = json.loads(route_res["text"])
            active_agents = plan.get("agents_to_run", ["GeneralAgent"])
            parallelizable = plan.get("parallelizable", False)
        except:
            log.warning("⚠️ Router failed JSON parse. Defaulting to GeneralChat.")
            active_agents = ["GeneralAgent"]
            plan = {"intent_summary": "Fallback"}

        log.info(f"📋 Plan: {active_agents} | Parallel: {parallelizable}")

        # =========================================================================
        # 🚀 STAGE 1: CREATION (Parallel)
        # Research, CodeGen, Explain (Conceptual) - Independent of each other
        # =========================================================================
        stage1_tasks = []
        
        # A. Research (Flash)
        if "ResearchAgent" in active_agents:
            stage1_tasks.append(("ResearchAgent", self.run_llm("Research", MODEL_FAST, SYSTEM_PROMPTS["ResearchAgent"], user_prompt)))

        # B. General Chat (Flash)
        if "GeneralAgent" in active_agents and "CodeGenAgent" not in active_agents:
            stage1_tasks.append(("GeneralAgent", self.run_llm("Chat", MODEL_FAST, SYSTEM_PROMPTS["GeneralAgent"], user_prompt)))

        # C. Coding (Pro) - The Heavy Lifter
        if "CodeGenAgent" in active_agents:
            # CodeGen gets the raw user prompt. 
            # Note: If we wanted to feed Research into CodeGen, we'd have to make them sequential.
            # The user explicitly asked for PARALLEL execution of Research and CodeGen.
            stage1_tasks.append(("CodeGenAgent", self.run_llm("CodeGen", MODEL_HEAVY, SYSTEM_PROMPTS["CodeGenAgent"], user_prompt, max_tokens=4000)))

        # D. Explain (Flash) - High level explanation of the concept, not necessarily the code yet
        # If ExplainAgent needs the code, it should be in Stage 2. 
        # But user said: "ExplainAgent... These three do NOT depend on each other. So run them at the same time."
        # So we run ExplainAgent on the USER PROMPT here.
        if "ExplainAgent" in active_agents:
             stage1_tasks.append(("ExplainAgent", self.run_llm("Explain", MODEL_FAST, SYSTEM_PROMPTS["ExplainAgent"], user_prompt)))

        # Execute Stage 1
        if stage1_tasks:
            log.info(f"🚀 Starting Stage 1 with {len(stage1_tasks)} agents...")
            # Unpack tasks
            names = [t[0] for t in stage1_tasks]
            coros = [t[1] for t in stage1_tasks]
            
            results_s1 = await asyncio.gather(*coros)
            
            for name, res in zip(names, results_s1):
                results[name] = res

        # Check for generated code
        base_code = results.get("CodeGenAgent", {}).get("text", "")
        
        # =========================================================================
        # ⚡ STAGE 2: DERIVATIVES (Parallel)
        # Depends on CodeGen output
        # =========================================================================
        stage2_tasks = []
        
        if base_code:
            # Context is the code + original prompt
            context_for_derivs = f"Original Request: {user_prompt}\n\nCode:\n{base_code}"
            
            # Helper
            def make_task(agent_name, model=MODEL_FAST):
                return (agent_name, self.run_llm(agent_name, model, SYSTEM_PROMPTS[agent_name], context_for_derivs))

            if "SafetyAgent" in active_agents:
                stage2_tasks.append(make_task("SafetyAgent"))
            
            if "TestGenAgent" in active_agents:
                stage2_tasks.append(make_task("TestGenAgent"))
            
            if "DocstringAgent" in active_agents:
                stage2_tasks.append(make_task("DocstringAgent"))
            
            if "TranslateAgent" in active_agents:
                # Translator might benefit from Pro, but Flash is usually fine for translation. User suggested Flash/Pro.
                # Let's stick to Flash for speed unless it's critical.
                stage2_tasks.append(make_task("TranslateAgent", MODEL_FAST))

            # Execute Stage 2
            if stage2_tasks:
                log.info(f"⚡ Starting Stage 2 with {len(stage2_tasks)} agents...")
                names = [t[0] for t in stage2_tasks]
                coros = [t[1] for t in stage2_tasks]
                
                results_s2 = await asyncio.gather(*coros)
                
                for name, res in zip(names, results_s2):
                    results[name] = res

        # Update base code if docstrings were added
        if results.get("DocstringAgent", {}).get("ok"):
            base_code = results["DocstringAgent"]["text"]

        # =========================================================================
        # ⚖️ STAGE 3: EVALUATION (Sequential)
        # Depends on everything
        # =========================================================================
        if "EvaluatorAgent" in active_agents and base_code:
            log.info("⚖️ Starting Stage 3: Evaluator...")
            eval_ctx = f"Req: {user_prompt}\nCode: {base_code}\nTests: {results.get('TestGenAgent', {}).get('text','')}"
            results["EvaluatorAgent"] = await self.run_llm("Evaluator", MODEL_FAST, SYSTEM_PROMPTS["EvaluatorAgent"], eval_ctx)

        # =========================================================================
        # 📦 FINAL SUMMARY
        # =========================================================================
        latency = time.time() - start_time
        log.info(f"✅ Plan Complete. Latency: {latency:.2f}s")
        
        return {
            "summary": {
                "intent": plan.get("intent_summary", "Task"),
                "generated_code": base_code,
                "explanation": results.get("ExplainAgent", {}).get("text") or results.get("GeneralAgent", {}).get("text"),
                "tests": results.get("TestGenAgent", {}).get("text"),
                "translation": results.get("TranslateAgent", {}).get("text"),
                "safety": results.get("SafetyAgent", {}).get("text"),
                "evaluation": results.get("EvaluatorAgent", {}).get("text"),
                "latency": f"{latency:.2f}s"
            },
            "raw_results": results
        }