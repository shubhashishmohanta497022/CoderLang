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
            # Clear workflow session when switching chats
            if "workflow_session" in st.session_state:
                del st.session_state.workflow_session
            st.rerun()

    st.divider()
    
    # --- REPO IMPORT (Paperclip Functionality) ---
    with st.expander("📎 Import Repository"):
        repo_url = st.text_input("Git Repo URL", key="repo_url_input")
        if st.button("Fetch Repo", key="fetch_repo_btn"):
            with st.spinner("Fetching repository..."):
                from utils.repo_loader import RepoLoader
                loader = RepoLoader()
                path, err = loader.fetch_repo(repo_url)
                if path:
                    st.session_state.repo_path = path
                    st.session_state.repo_files = loader.get_file_tree(path)
                    st.success("Repo fetched!")
                else:
                    st.error(f"Failed: {err}")
        
        if "repo_files" in st.session_state:
            selected_files = st.multiselect("Select Files", st.session_state.repo_files)
            analysis_goal = st.selectbox("Goal", [
                "Explain Codebase",
                "Refactor Code",
                "Find Bugs",
                "Add Comments",
                "Convert to Python",
                "Extend Functionality"
            ])
            custom_goal = st.text_input("Custom Goal")
            
            if st.button("Analyze", type="primary"):
                if not selected_files:
                    st.warning("Select files first.")
                else:
                    from utils.repo_loader import RepoLoader
                    loader = RepoLoader()
                    context = ""
                    for f in selected_files:
                        content = loader.read_file(st.session_state.repo_path, f)
                        context += f"\n--- FILE: {f} ---\n{content}\n"
                    
                    final_goal = custom_goal if custom_goal else analysis_goal
                    full_prompt = f"Analyze the following repository files.\nGOAL: {final_goal}\n\nCONTEXT:\n{context}"
                    process_prompt(full_prompt)

    # --- SETTINGS ---
    with st.expander("⚙️ Settings"):
        st.subheader("Data Management")
        # Export
        if st.button("Export Memory Dump"):
            dump = st.session_state.memory.get_full_memory_dump()
            st.download_button(
                label="Download JSON",
                data=json.dumps(dump, indent=2),
                file_name=f"coderlang_memory_{int(time.time())}.json",
                mime="application/json"
            )
        
        # Import
        uploaded_file = st.file_uploader("Import Chat", type=["json"])
        if uploaded_file is not None:
            try:
                content = json.load(uploaded_file)
                success, msg = st.session_state.memory.import_chat_session(content)
                if success:
                    st.success(msg)
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(msg)
            except Exception as e:
                st.error(f"Import failed: {e}")
        
        st.divider()
        if st.button("Clear Session Memory"):
            st.session_state.memory._init_file(st.session_state.memory.short_term_path)
            st.toast("Memory cleared!", icon="🧹")
        
        st.info("**Configuration:**\n- Router: Gemini 2.5 Flash\n- Coding: Gemini 3 Pro Preview")

# --- CHAT INTERFACE ---

def render_message_content(summary, raw, key_suffix=""):
    if summary.get("generated_code"):
        task_type = summary.get("intent", "General Task")
        
        # Header with Download Response Button
        c1, c2 = st.columns([4, 1])
        with c1:
            st.markdown(f"**Task:** {task_type}")
        with c2:
            st.download_button(
                "📥 JSON", 
                data=json.dumps(summary, indent=2), 
                file_name=f"response_{key_suffix}.json", 
                key=f"dl_res_{key_suffix}"
            )

        if summary.get("explanation"):
            st.markdown(summary["explanation"])
        
        tab1, tab2, tab3, tab4 = st.tabs(["💻 Source", "📊 Evaluation", "🧪 Tests & Docs", "📜 System Logs"])
        
        with tab1:
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
        with tab2:
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
        with tab3:
            if summary.get("tests"):
                st.subheader("Unit Tests")
                st.code(summary["tests"], language="python")
            else:
                st.text("No tests generated.")
        with tab4:
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
# Header Actions
c_head, c_act = st.columns([10, 2])
with c_head:
    pass # Title already rendered above
with c_act:
    # Download Current Chat
    current_chat_json = st.session_state.memory.export_chat_session(st.session_state.current_chat_id)
    if current_chat_json:
        st.download_button(
            "📥 Chat",
            data=current_chat_json,
            file_name=f"chat_{st.session_state.current_chat_id}.json",
            mime="application/json",
            key="dl_chat_top"
        )

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