#!/usr/bin/env python3
"""
Minimal patch script to add auto-load repo feature and Enter key support.
Only modifies the necessary sections without touching other code.
"""

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Step 1: Find where to insert process_prompt function (before "# Sidebar")
sidebar_line = None
for i, line in enumerate(lines):
    if line.strip() == '# Sidebar':
        sidebar_line = i
        break

if sidebar_line:
    # Insert the helper function before "# Sidebar"
    process_prompt_func = '''# Helper function for processing prompts
def process_prompt(prompt):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.memory.save_message(st.session_state.current_chat_id, "user", prompt)
    orch = Orchestrator()
    st.session_state.workflow_session = orch.create_session(prompt)
    st.rerun()

'''
    lines.insert(sidebar_line, process_prompt_func)

# Step 2: Find and replace the repo import section
repo_start = None
repo_end = None
for i, line in enumerate(lines):
    if '# --- REPO IMPORT (Paperclip Functionality) ---' in line:
        repo_start = i
    if repo_start and i > repo_start and '# --- SETTINGS ---' in line:
        repo_end = i
        break

if repo_start and repo_end:
    # New repo import section with auto-load and Enter key
    new_repo_section = '''    # --- REPO IMPORT (Paperclip Functionality) ---
    with st.expander("📎 Import Repository"):
        # JavaScript for Enter key support
        st.components.v1.html("""
            <script>
            setTimeout(() => {
                const inputs = window.parent.document.querySelectorAll('input[type="text"]');
                inputs.forEach(input => {
                    if (input.getAttribute('aria-label') === 'Git Repo URL') {
                        input.addEventListener('keypress', (e) => {
                            if (e.key === 'Enter') {
                                e.preventDefault();
                                const buttons = window.parent.document.querySelectorAll('button');
                                buttons.forEach(btn => {
                                    if (btn.textContent.includes('Fetch Repo')) {
                                        btn.click();
                                    }
                                });
                            }
                        });
                    }
                });
            }, 500);
            </script>
        """, height=0, width=0)
        
        repo_url = st.text_input("Git Repo URL", key="repo_url_input")
        
        if st.button("Fetch Repo", key="fetch_repo_btn"):
            if repo_url:
                with st.spinner("🔄 Automatically fetching all repository files..."):
                    from utils.repo_loader import RepoLoader
                    loader = RepoLoader()
                    
                    # Use auto-load functionality
                    repo_content, err = loader.load_full_repo(repo_url, max_files=150)
                    
                    if repo_content:
                        st.session_state.repo_content = repo_content
                        st.session_state.repo_url = repo_url
                        st.success(f"✅ Repo fetched! Automatically loaded {len(repo_content)} files.")
                    else:
                        st.error(f"❌ Failed: {err}")
        
        # Show analysis options if repo content is loaded
        if "repo_content" in st.session_state and st.session_state.repo_content:
            st.info(f"📁 **{len(st.session_state.repo_content)} files** loaded from repository")
            
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
                # Build context from all loaded files
                context = ""
                for filepath, content in st.session_state.repo_content.items():
                    context += f"\\n--- FILE: {filepath} ---\\n{content}\\n"
                
                final_goal = custom_goal if custom_goal else analysis_goal
                full_prompt = f"Analyze the following repository files.\\nGOAL: {final_goal}\\n\\nCONTEXT:\\n{context}"
                process_prompt(full_prompt)

'''
    # Replace the old section
    lines[repo_start:repo_end] = [new_repo_section]

# Write the fixed file
with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ app.py patched successfully!")
print("Changes made:")
print("  1. Added process_prompt() helper function")
print("  2. Replaced manual file selection with automatic loading")
print("  3. Added Enter key JavaScript listener")
