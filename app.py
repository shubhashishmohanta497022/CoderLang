import streamlit as st
import time
import os
import json
import asyncio
from orchestrator.coordinator import Orchestrator
from memory.memory_store import MemoryStore

# Page Config
st.set_page_config(
    page_title="CoderLang Universal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS STYLING ---
st.markdown("""
<style>
    .stTextArea textarea { font-family: 'Fira Code', monospace; }
    div[data-testid="metric-container"] {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 8px;
        color: white;
    }
    .success-box { padding: 10px; background-color: rgba(40, 167, 69, 0.1); border-left: 5px solid #28a745; border-radius: 4px; }
    .info-box { padding: 10px; background-color: rgba(23, 162, 184, 0.1); border-left: 5px solid #17a2b8; border-radius: 4px; }
    .chat-row { padding: 8px; border-radius: 4px; margin-bottom: 5px; cursor: pointer; }
    .chat-row:hover { background-color: rgba(255, 255, 255, 0.1); }
</style>
""", unsafe_allow_html=True)

# --- LOCAL STORAGE BRIDGE ---
# We use a hidden div to inject JS that saves/loads state
def local_storage_manager():
    # 1. SAVE: If we have a workflow state, save it
    if "workflow_session" in st.session_state and st.session_state.workflow_session:
        state_json = json.dumps(st.session_state.workflow_session.to_json())
        # Escape for JS: Backslashes first, then backticks
        state_json_safe = state_json.replace("\\", "\\\\").replace("`", "\\`").replace("${", r"\${")
        
        st.components.v1.html(
            f"""
            <script>
            try {{
                localStorage.setItem("coderlang_workflow", `{state_json_safe}`);
                console.log("✅ Workflow saved to LocalStorage");
            }} catch (e) {{
                console.error("❌ Save failed", e);
            }}
            </script>
            """,
            height=0,
            width=0
        )

    # 2. LOAD: Check query params for restored data
    query_params = st.query_params
    if "restored_state" in query_params:
        try:
            restored_data = json.loads(query_params["restored_state"])
            # Clear param to avoid re-loading on every run
            if "restored_state" in st.query_params:
                del st.query_params["restored_state"]
            
            if "workflow_session" not in st.session_state:
                orch = Orchestrator()
                st.session_state.workflow_session = orch.create_session(
                    prompt=restored_data["prompt"],
                    state=restored_data["state"]
                )
                st.toast("🔄 Workflow Resumed from LocalStorage!", icon="💾")
                st.rerun()
        except Exception as e:
            st.error(f"Failed to restore state: {e}")

    # 3. INJECT LOADER: If no session, try to load from LS
    if "workflow_session" not in st.session_state:
        st.components.v1.html(
            """
            <script>
            const saved = localStorage.getItem("coderlang_workflow");
            if (saved) {
                // We found a saved session! Send it back to Streamlit via URL param
                // Note: URL params have size limits. For large state, we might need a different bridge.
                // But for this demo, we'll try this. If it's too big, we'd need a custom component.
                // Let's check if we are already in a restore loop to avoid infinite reload
                const urlParams = new URLSearchParams(window.location.search);
                if (!urlParams.has("restored_state")) {
                    // Set the param and reload
                    // WARNING: This is a simple bridge. Large state might fail here.
                    // Ideally we'd use a custom Streamlit component for bi-directional data.
                    // For now, let's assume it fits or use a simplified ID approach if we had a backend DB.
                    // Since we don't have a DB, we pass the JSON.
                    
                    // Truncate if too huge to prevent crash?
                    if (saved.length < 500000) { 
                        const newUrl = new URL(window.location.href);
                        newUrl.searchParams.set("restored_state", saved);
                        window.location.href = newUrl.toString();
                    } else {
                        console.warn("⚠️ State too large for URL bridge.");
                    }
                }
            }
            </script>
            """,
            height=0,
            width=0
        )

# Initialize Memory
if "memory" not in st.session_state:
    st.session_state.memory = MemoryStore()

# Initialize Session State for Chat ID
if "current_chat_id" not in st.session_state:
    sessions = st.session_state.memory.list_chat_sessions()
    if sessions:
        st.session_state.current_chat_id = sessions[0]["id"]
    else:
        st.session_state.current_chat_id = st.session_state.memory.create_chat_session()

# Load Messages
st.session_state.messages = st.session_state.memory.load_chat_history(st.session_state.current_chat_id)

# Run LocalStorage Manager
local_storage_manager()

# Header
col1, col2 = st.columns([1, 12])
with col1:
    st.image("https://cdn-icons-png.flaticon.com/512/2083/2083213.png", width=50)
with col2:
    st.title("CoderLang Universal Engine")
    st.caption("Hyper-fast Async Agent Pipeline powered by Gemini 2.5 Flash & 3 Pro")

# Sidebar
with st.sidebar:
    st.header("🧠 Memory Context")
    if st.button("➕ New Chat", use_container_width=True):
        new_id = st.session_state.memory.create_chat_session()
        st.session_state.current_chat_id = new_id
        # Clear workflow session on new chat
        if "workflow_session" in st.session_state:
            del st.session_state.workflow_session
        st.rerun()

    st.divider()
    st.subheader("Past Chats")
    sessions = st.session_state.memory.list_chat_sessions()
    for session in sessions:
        label = session["title"]
        if session["id"] == st.session_state.current_chat_id:
            label = f"🔹 {label}"
        if st.button(label, key=session["id"], use_container_width=True):
            st.session_state.current_chat_id = session["id"]
            # Clear workflow session when switching chats (unless we want to persist per chat? For now, clear)
            if "workflow_session" in st.session_state:
                del st.session_state.workflow_session
            st.rerun()

    st.divider()
    if st.button("Clear Session Memory"):
        st.session_state.memory._init_file(st.session_state.memory.short_term_path)
        st.toast("Short-term memory cleared!", icon="🧹")
    
    st.subheader("Active Configuration")
    st.info("""
    **Router:** Gemini 2.5 Flash
    **Coding:** Gemini 3 Pro Preview
    **Analysis:** Gemini 2.5 Flash
    **Pipeline:** Async DAG
    """)

# --- CHAT INTERFACE ---

# Load Execution Panel Template
try:
    with open("frontend/execution_panel.html", "r", encoding="utf-8") as f:
        EXECUTION_PANEL_TEMPLATE = f.read()
except FileNotFoundError:
    EXECUTION_PANEL_TEMPLATE = "<div>Error: frontend/execution_panel.html not found</div>"

def render_execution_panel(code, language):
    """Injects code into the HTML template and renders it."""
    # Escape code for JS template literal
    # 1. Escape backslashes
    # 2. Escape backticks
    # 3. Escape ${ for template literals
    safe_code = code.replace("\\", "\\\\").replace("`", "\\`").replace("${", r"\${")
    
    html_content = EXECUTION_PANEL_TEMPLATE.replace("__CODE_GOES_HERE__", safe_code)
    html_content = html_content.replace("__LANG_GOES_HERE__", language)
    
    st.components.v1.html(html_content, height=450, scrolling=False)

def render_message_content(summary, raw, key_suffix=""):
    if summary.get("generated_code"):
        task_type = summary.get("intent", "General Task")
        st.markdown(f"**Task:** {task_type}")
        if summary.get("explanation"):
            st.markdown(summary["explanation"])
        
        # Determine Language
        language = "python"
        code_to_run = summary["generated_code"]
        
        # Check for JS signatures
        if "console.log" in code_to_run or "document.getElementById" in code_to_run or "function " in code_to_run:
             if "def " not in code_to_run:
                 language = "javascript"

        tab1, tab2, tab3, tab4, tab5 = st.tabs(["▶️ Run Code", "💻 Source", "📊 Evaluation", "🧪 Tests & Docs", "📜 System Logs"])
        
        with tab1:
            st.caption(f"Execution Engine ({language})")
            render_execution_panel(code_to_run, language)

        with tab2:
            st.subheader("Source Code")
            st.code(summary["generated_code"], language="python", line_numbers=True)
            st.download_button("Download .py", summary["generated_code"], "solution.py", key=f"dl_btn_{key_suffix}")
            if summary.get("translation"):
                st.divider()
                st.subheader("C++ Translation")
                st.code(summary["translation"], language="cpp")
            if summary.get("explanation"):
                with st.expander("💡 Logic Explanation"):
                    st.markdown(summary["explanation"])
        with tab3:
            eval_text = summary.get("evaluation", "No evaluation.")
            score = "N/A"
            if "Score:" in eval_text:
                score = eval_text.split("Score:")[1].split("/")[0].strip() + "/10"
            c1, c2, c3 = st.columns(3)
            c1.metric("Quality Score", score)
            c2.metric("Agents Active", len(raw))
            c3.metric("Total Latency", summary.get("latency", "N/A"))
            st.info(eval_text)
            if summary.get("safety"):
                st.warning(f"🔒 Safety Scan: {summary['safety']}")
        with tab4:
            if summary.get("tests"):
                st.subheader("Unit Tests")
                st.code(summary["tests"], language="python")
            else:
                st.text("No tests generated.")
        with tab5:
            st.json(raw)
    else:
        if summary.get("explanation"):
            st.markdown(summary["explanation"])
        if summary.get("research"):
            with st.expander("📚 Research Data"):
                st.markdown(summary["research"])

def process_prompt(prompt, is_refinement=False):
    # 1. Add User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.memory.save_message(st.session_state.current_chat_id, "user", prompt)
    
    # 2. Initialize Workflow Session
    orch = Orchestrator()
    st.session_state.workflow_session = orch.create_session(prompt)
    
    st.rerun()

# Display History
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        if message.get("metadata") and "summary" in message["metadata"]:
            render_message_content(message["metadata"]["summary"], message["metadata"].get("raw_results", {}), key_suffix=str(i))
        else:
            st.markdown(message["content"])

# --- WORKFLOW EXECUTION LOOP ---
if "workflow_session" in st.session_state:
    session = st.session_state.workflow_session
    
    # If not complete, show status and run next step
    if session.state["stage"] != "COMPLETE":
        with st.status(f"🚀 Processing: {session.state['stage']}...", expanded=True) as status:
            st.write(f"Current Stage: {session.state['stage']}")
            # Show logs
            for log in session.state["logs"][-3:]:
                st.text(log)
            
            # Run Next Step
            asyncio.run(session.run_next_step())
            
            # Save state implicitly via local_storage_manager on rerun
            st.rerun()
            
    # If Complete, finalize and clear session
    else:
        summary = session.get_summary()
        raw = session.state["results"]
        
        # Add Assistant Message
        response_text = summary.get("explanation", "Response generated.")
        if summary.get("generated_code"):
            response_text = f"**Task:** {summary.get('intent')}\n\n{response_text}\n\n*(Code generated - check tabs)*"

        st.session_state.messages.append({
            "role": "assistant", 
            "content": response_text,
            "metadata": {"summary": summary, "raw_results": raw}
        })
        
        st.session_state.memory.save_message(
            st.session_state.current_chat_id, 
            "assistant", 
            response_text, 
            metadata={"summary": summary, "raw_results": raw}
        )
        
        # Clear workflow session
        del st.session_state.workflow_session
        st.rerun()

# Regeneration Buttons
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("🔄 Regenerate", help="Re-run the last request"):
            last_user_msg = next((m for m in reversed(st.session_state.messages) if m["role"] == "user"), None)
            if last_user_msg:
                process_prompt(last_user_msg["content"])
    with col2:
        if st.button("✨ Make it Concise", help="Regenerate with a focus on brevity"):
            last_user_msg = next((m for m in reversed(st.session_state.messages) if m["role"] == "user"), None)
            if last_user_msg:
                new_prompt = f"{last_user_msg['content']}\n\n(Please provide a concise, minimal solution)"
                process_prompt(new_prompt)

# Input (Disabled if workflow running)
if "workflow_session" not in st.session_state:
    if prompt := st.chat_input("Ask me to code, research, explain, or translate..."):
        process_prompt(prompt)
else:
    st.info("⚠️ Workflow in progress... Please wait.")