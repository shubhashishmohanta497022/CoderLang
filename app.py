import streamlit as st
import time
import os
import json
from orchestrator.router import run_orchestrator
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
    
    /* Metrics Styling */
    div[data-testid="metric-container"] {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 8px;
        color: white;
    }
    
    /* Success/Error Boxes */
    .success-box { padding: 10px; background-color: rgba(40, 167, 69, 0.1); border-left: 5px solid #28a745; border-radius: 4px; }
    .info-box { padding: 10px; background-color: rgba(23, 162, 184, 0.1); border-left: 5px solid #17a2b8; border-radius: 4px; }
    
    /* Chat List Styling */
    .chat-row {
        padding: 8px;
        border-radius: 4px;
        margin-bottom: 5px;
        cursor: pointer;
    }
    .chat-row:hover {
        background-color: rgba(255, 255, 255, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# Initialize Memory
if "memory" not in st.session_state:
    st.session_state.memory = MemoryStore()

# Initialize Session State for Chat ID
if "current_chat_id" not in st.session_state:
    # Try to load the most recent chat, or create a new one
    sessions = st.session_state.memory.list_chat_sessions()
    if sessions:
        st.session_state.current_chat_id = sessions[0]["id"]
    else:
        st.session_state.current_chat_id = st.session_state.memory.create_chat_session()

# Load Messages for Current Chat
st.session_state.messages = st.session_state.memory.load_chat_history(st.session_state.current_chat_id)

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
        st.rerun()

    st.divider()
    st.subheader("Past Chats")
    
    sessions = st.session_state.memory.list_chat_sessions()
    for session in sessions:
        # Highlight current chat
        label = session["title"]
        if session["id"] == st.session_state.current_chat_id:
            label = f"🔹 {label}"
            
        if st.button(label, key=session["id"], use_container_width=True):
            st.session_state.current_chat_id = session["id"]
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

# Helper: Render Message Content
def render_message_content(summary, raw):
    # If Code was Generated (The Full Suite)
    if summary.get("generated_code"):
        task_type = summary.get("intent", "General Task")
        st.markdown(f"**Task:** {task_type}")
        
        if summary.get("explanation"):
            st.markdown(summary["explanation"])
            
        tab1, tab2, tab3, tab4 = st.tabs(["💻 Code & Solution", "📊 Evaluation", "🧪 Tests & Docs", "📜 System Logs"])
        
        # TAB 1: Final Solution
        with tab1:
            st.subheader("Solution")
            st.code(summary["generated_code"], language="python", line_numbers=True)
            st.download_button("Download .py", summary["generated_code"], "solution.py")
            
            if summary.get("translation"):
                st.divider()
                st.subheader("C++ Translation")
                st.code(summary["translation"], language="cpp")

            if summary.get("explanation"):
                with st.expander("💡 Logic Explanation"):
                    st.markdown(summary["explanation"])

        # TAB 2: Scorecard
        with tab2:
            # Extract Score
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

        # TAB 3: Derivatives
        with tab3:
            if summary.get("tests"):
                st.subheader("Unit Tests")
                st.code(summary["tests"], language="python")
            else:
                st.text("No tests generated.")

        # TAB 4: Raw Debug Logs
        with tab4:
            st.json(raw)

    # If it was just a chat/research/explain task (No Code)
    else:
        if summary.get("explanation"):
            st.markdown(summary["explanation"])
            
        if summary.get("research"):
            with st.expander("📚 Research Data"):
                st.markdown(summary["research"])

# Helper: Process Prompt
def process_prompt(prompt, is_refinement=False):
    # 1. Add User Message to State & Memory
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.memory.save_message(st.session_state.current_chat_id, "user", prompt)
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        status_container = st.status("🚀 Initializing Universal Pipeline...", expanded=True)
        
        try:
            start_time = time.time()
            
            # CALL THE ROUTER
            output = run_orchestrator(prompt)
            
            # Parse Results
            summary = output.get("summary", {})
            raw = output.get("raw_results", {})
            
            # Status Update
            latency = summary.get("latency", "0.00s")
            task_type = summary.get("intent", "General Task")
            status_container.update(label=f"✅ Complete in {latency} | Task: {task_type}", state="complete", expanded=False)

            # --- DISPLAY RESULTS ---
            render_message_content(summary, raw)
            
            # 2. Add Assistant Message to State & Memory
            # We store a fallback text representation in 'content' for simple viewers,
            # but we rely on 'metadata' for the full UI.
            response_text = summary.get("explanation", "Response generated.")
            if summary.get("generated_code"):
                response_text = f"**Task:** {task_type}\n\n{response_text}\n\n*(Code generated - check tabs)*"

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
            
            # Force a rerun to update UI (and sidebar title if needed)
            st.rerun()

        except Exception as e:
            status_container.update(label="❌ System Error", state="error")
            st.error(f"Pipeline Failed: {e}")

# Display History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # Check if we have metadata to render the full UI
        if message.get("metadata") and "summary" in message["metadata"]:
            render_message_content(
                message["metadata"]["summary"], 
                message["metadata"].get("raw_results", {})
            )
        else:
            # Fallback for old messages or simple text
            st.markdown(message["content"])

# Regeneration Buttons (Only if history exists and last msg is assistant)
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("🔄 Regenerate", help="Re-run the last request"):
            # Find last user message
            last_user_msg = next((m for m in reversed(st.session_state.messages) if m["role"] == "user"), None)
            if last_user_msg:
                process_prompt(last_user_msg["content"])
    with col2:
        if st.button("✨ Make it Concise", help="Regenerate with a focus on brevity"):
            last_user_msg = next((m for m in reversed(st.session_state.messages) if m["role"] == "user"), None)
            if last_user_msg:
                new_prompt = f"{last_user_msg['content']}\n\n(Please provide a concise, minimal solution)"
                process_prompt(new_prompt)

# Input
if prompt := st.chat_input("Ask me to code, research, explain, or translate..."):
    process_prompt(prompt)