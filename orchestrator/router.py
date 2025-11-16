from agents.coding_agent import CodingAgent
from agents.translate_agent import TranslateAgent
from agents.test_generator_agent import TestGeneratorAgent
from agents.explain_agent import ExplainAgent # --- ADD THIS IMPORT ---

def run_main_flow(user_prompt: str):
    """
    The main orchestrator flow.
    """
    print(f"\n🧠 Orchestrator: Received prompt: '{user_prompt}'")
    
    results = {}
    
    # --- Step 1: Call CodingAgent ---
    print("🧠 Orchestrator: Routing to CodingAgent...")
    coder = CodingAgent()
    generated_code = coder.run(user_prompt)
    results["python_code"] = generated_code
    
    # --- Step 2: Call TranslateAgent ---
    print("🧠 Orchestrator: Routing to TranslateAgent...")
    translator = TranslateAgent()
    target_lang = "JavaScript" 
    translated_code = translator.run(generated_code, target_lang)
    results["translated_code"] = translated_code
    
    # --- Step 3: Call TestGeneratorAgent ---
    print("🧠 Orchestrator: Routing to TestGeneratorAgent...")
    test_generator = TestGeneratorAgent()
    unit_tests = test_generator.run(generated_code)
    results["unit_tests"] = unit_tests
    
    # --- Step 4: Call ExplainAgent ---
    print("🧠 Orchestrator: Routing to ExplainAgent...")
    explainer = ExplainAgent()
    explanation = explainer.run(generated_code)
    results["explanation"] = explanation
    
    print("🧠 Orchestrator: Flow complete.")
    return results