# Auto-patch script for app.py
# Run this with: python apply_auto_load.py

import re

# Read the current app.py
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Define the old section to replace (lines 167-207)
old_section = '''    # --- REPO IMPORT (Paperclip Functionality) ---
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
                        context += f"\\n--- FILE: {f} ---\\n{content}\\n"
                    
                    final_goal = custom_goal if custom_goal else analysis_goal
                    full_prompt = f"Analyze the following repository files.\\nGOAL: {final_goal}\\n\\nCONTEXT:\\n{context}"
                    process_prompt(full_prompt)'''

# Define new section with auto-load
new_section = '''    # --- REPO IMPORT (Paperclip Functionality) ---
    with st.expander("📎 Import Repository"):
        # Use form to allow Enter key to submit
        with st.form("fetch_repo_form", clear_on_submit=False):
            repo_url = st.text_input("Git Repo URL", placeholder="https://github.com/username/repository")
            col1, col2 = st.columns(2)
            with col1:
                fetch_submitted = st.form_submit_button("🔽 Fetch Repo (Manual)", use_container_width=True)
            with col2:
                auto_load_submitted = st.form_submit_button("🚀 Auto-Load Full Repo", use_container_width=True, type="primary")
        
        # Auto-Load Full Repo (Direct to orchestrator)
        if auto_load_submitted and repo_url:
            with st.spinner("🔄 Auto-loading full repository..."):
                from utils.repo_loader import RepoLoader
                loader = RepoLoader()
                
                # Show progress
                progress_text = st.empty()
                progress_text.info("Fetching repository tree from GitHub API...")
                
                repo_content, err = loader.load_full_repo(repo_url, max_files=150)
                
                if repo_content:
                    progress_text.success(f"✅ Loaded {len(repo_content)} files!")
                    
                    # Build context from all files
                    context = ""
                    for file_path, content in repo_content.items():
                        context += f"\\n--- FILE: {file_path} ---\\n{content}\\n"
                    
                    # Store for analysis
                    st.session_state.auto_loaded_repo = repo_content
                    st.session_state.auto_loaded_context = context
                    st.info("✅ Repository auto-loaded! Select a goal below and click Analyze.")
                else:
                    progress_text.error(f"❌ Failed: {err}")
        elif auto_load_submitted and not repo_url:
            st.warning("Please enter a Git repository URL.")
        
        # Display goal selection if auto-loaded
        if "auto_loaded_repo" in st.session_state:
            st.divider()
            st.markdown(f"**📦 Auto-loaded: {len(st.session_state.auto_loaded_repo)} files**")
            
            analysis_goal = st.selectbox("Goal", [
                "Explain Codebase",
                "Refactor Code",
                "Find Bugs",
                "Add Comments",
                "Convert to Python",
                "Extend Functionality",
                "Generate Documentation",
                "Code Review"
            ], key="auto_goal")
            custom_goal = st.text_input("Custom Goal", key="auto_custom_goal")
            
            if st.button("🎯 Analyze Auto-Loaded Repo", type="primary", use_container_width=True):
                final_goal = custom_goal if custom_goal else analysis_goal
                full_prompt = f"Analyze the following repository files.\\nGOAL: {final_goal}\\n\\nCONTEXT:\\n{st.session_state.auto_loaded_context}"
                
                # Clear auto-loaded state
                del st.session_state.auto_loaded_repo
                del st.session_state.auto_loaded_context
                
                process_prompt(full_prompt)
        
        # Manual Fetch (Old workflow)
        if fetch_submitted and repo_url:
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
        elif fetch_submitted and not repo_url:
            st.warning("Please enter a Git repository URL.")
        
        # Manual file selection (old workflow)
        if "repo_files" in st.session_state:
            st.divider()
            st.markdown("**📝 Manual File Selection**")
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
                        context += f"\\n--- FILE: {f} ---\\n{content}\\n"
                    
                    final_goal = custom_goal if custom_goal else analysis_goal
                    full_prompt = f"Analyze the following repository files.\\nGOAL: {final_goal}\\n\\nCONTEXT:\\n{context}"
                    process_prompt(full_prompt)'''

# Performthe replacement
if old_section in content:
    new_content = content.replace(old_section, new_section)
    
    # Write back
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Successfully applied auto-load feature to app.py!")
    print("Now run: docker build -t coderlang .")
else:
    print("❌ Could not find the section to replace.")
    print("The file may have been modified. Please check app.py manually.")
