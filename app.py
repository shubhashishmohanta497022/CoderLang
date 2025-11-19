import streamlit as st
import time
import os
import json
from orchestrator.router import run_orchestrator
from memory.memory_store import MemoryStore

# Page Config
st.set_page_config(
    page_title="CoderLang Enterprise",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS FIXES ---
st.markdown("""
<style>
    .stTextArea textarea { font-family: 'Fira Code', monospace; }
    
    /* Fix for Metric Boxes (Evaluator Score) */
    div[data-testid="metric-container"] {
        background-color: rgba(255, 255, 255, 0.05); /* Translucent dark */
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 8px;
        color: white;
    }
    
    /* Success/Error styling */
    .success-box { padding: 10px; background-color: rgba(40, 167, 69, 0.1); border-left: 5px solid #28a745; border-radius: 4px; }
    .error-box { padding: 10px; background-color: rgba(220, 53, 69, 0.1); border-left: 5px solid #dc3545; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# Title
col1, col2 = st.columns([1, 10])
with col1:
    st.image("https://cdn-icons-png.flaticon.com/512/2083/2083213.png", width=60)
with col2:
    st.title("CoderLang Enterprise")
    st.caption("Multi-Agent Coding Assistant powered by Google Gemini")

# Sidebar
with st.sidebar:
    st.header("🧠 Memory Context")
    memory = MemoryStore()
    
    if st.button("Clear Short-Term Memory"):
        memory._init_file(memory.short_term_path)
        st.toast("Memory cleared!", icon="🧹")
    
    st.subheader("Session Data")
    try:
        short_term = memory._load(memory.short_term_path)
        st.json(short_term)
    except:
        st.text("No memory yet.")

    st.divider()
    st.info("Agents Active:\n- CodingAgent\n- SafetyAgent\n- TestGenerator\n- DebuggingAgent\n- ExplainAgent\n- Evaluator\n- ResearchAgent")

# --- MAIN CHAT INTERFACE ---

# 1. Initialize Chat History if not present
if "messages" not in st.session_state:
    st.session_state.messages = []

# 2. Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 3. Input Area (Enter sends, Shift+Enter for new line)
if prompt := st.chat_input("Enter your coding request (e.g., 'Write a Python script to parse a CSV')..."):
    
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Assistant Response
    with st.chat_message("assistant"):
        
        # Use st.status to show progress without cluttering the final UI
        with st.status("🤖 Agents are collaborating...", expanded=True) as status:
            st.write("Initializing Orchestrator...")
            st.write("Planning steps...")
            
            try:
                start_time = time.time()
                results = run_orchestrator(prompt)
                end_time = time.time()
                duration = round(end_time - start_time, 2)
                
                status.update(label=f"✅ Complete in {duration}s", state="complete", expanded=False)
            
            except Exception as e:
                status.update(label="❌ Failed", state="error")
                st.error(f"An error occurred: {e}")
                st.stop()

        # --- TABS for Result Display (Final Code First) ---
        tab_code, tab_live, tab_logs = st.tabs(["📄 Final Code", "📊 Orchestrator Live", "📜 Full Logs"])

        # TAB 1: Final Code & Metrics
        with tab_code:
            # Metrics Row
            m1, m2, m3 = st.columns(3)
            
            score = "N/A"
            if "final_evaluation" in results:
                try:
                    score = results["final_evaluation"].split("\n")[0].split(":")[1].strip()
                except:
                    score = "Check Logs"
            
            m1.metric("Evaluator Score", score)
            m2.metric("Agents Used", len(results) - 1)
            m3.metric("Auto-Debug Events", 1 if "step_auto_Debug" in results else 0)
            
            st.divider()

            # Find Final Code
            final_code = ""
            if "step_auto_Debug" in results:
                final_code = results["step_auto_Debug"]
                st.success("✨ Code was auto-corrected by DebuggingAgent", icon="🛠")
            else:
                for k, v in results.items():
                    if "CodingAgent" in k:
                        final_code = v
            
            if final_code:
                st.subheader("Generated Solution")
                st.code(final_code, language="python", line_numbers=True)
                
                st.download_button(
                    label="Download .py",
                    data=final_code,
                    file_name="coderlang_solution.py",
                    mime="text/x-python"
                )
            else:
                st.warning("No code generated.")

        # TAB 2: Orchestrator Live (Workflow)
        with tab_live:
            st.subheader("Agent Workflow Timeline")
            for key, value in results.items():
                if "step_" in key:
                    parts = key.split("_")
                    # Handles step_1_CodingAgent or step_auto_Debug
                    agent_name = parts[2] if len(parts) > 2 else parts[1]
                    
                    # Use expanders for cleaner look
                    with st.expander(f"🔹 {agent_name}", expanded=False):
                        st.code(value, language='python' if 'Code' in agent_name or 'Debug' in agent_name else 'text')

        # TAB 3: Full Logs
        with tab_logs:
            # Fix path: logic in logger.py creates nested logs folder
            # Root -> observability -> logs -> logs -> events.log
            # Check both possible paths to be safe
            possible_paths = [
                os.path.join("observability", "logs", "logs", "events.log"), # Nested
                os.path.join("observability", "logs", "events.log")          # Flat
            ]
            
            log_content = "Log file not found."
            for p in possible_paths:
                if os.path.exists(p):
                    with open(p, "r") as f:
                        lines = f.readlines()
                        log_content = "".join(lines[-50:]) # Last 50 lines
                    break
            
            st.text_area("System Logs", log_content, height=300)

    # Save assistant response to chat history (simplified for session state)
    st.session_state.messages.append({"role": "assistant", "content": "✅ Task executed successfully. Check the tabs above for details."})