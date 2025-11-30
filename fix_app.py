import re

# Read the original file
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and extract the process_prompt function
process_prompt_pattern = r'(def process_prompt\(prompt, is_refinement=False\):.*?st\.rerun\(\))'
match = re.search(process_prompt_pattern, content, re.DOTALL)
if match:
    process_prompt_func = match.group(1)
    # Remove it from its current location
    content = content.replace(match.group(0) + '\r\n\r\n', '')
    
    # Insert it before "# Sidebar"
    content = content.replace('# Sidebar\r\n', f'{process_prompt_func}\r\n\r\n# Sidebar\r\n')

# Now update the repo import section
old_repo_section = '''    # --- REPO IMPORT (Paperclip Functionality) ---
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

new_repo_section = '''    # --- REPO IMPORT (Paperclip Functionality) ---
    with st.expander("📎 Import Repository"):
        # Add JavaScript for Enter key support
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
        fetch_triggered = st.button("Fetch Repo", key="fetch_repo_btn")
        
        if fetch_triggered and repo_url:
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
                for filepath, content_data in st.session_state.repo_content.items():
                    context += f"\\n--- FILE: {filepath} ---\\n{content_data}\\n"
                
                final_goal = custom_goal if custom_goal else analysis_goal
                full_prompt = f"Analyze the following repository files.\\nGOAL: {final_goal}\\n\\nCONTEXT:\\n{context}"
                process_prompt(full_prompt)'''

content = content.replace(old_repo_section, new_repo_section)

# Write the updated file
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("File updated successfully!")
