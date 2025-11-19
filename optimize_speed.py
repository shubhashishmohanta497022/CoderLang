import os
import re

# Define the directories to scan
DIRECTORIES = ["agents", "orchestrator"]

def optimize_file(filepath):
    with open(filepath, "r") as f:
        content = f.read()

    # 1. Inject the config import if missing
    if "from config import" not in content:
        # Add import after standard imports
        if "import logging" in content:
            content = content.replace("import logging", "import logging\nfrom config import MODEL_NAME, SAFETY_SETTINGS")
        else:
            content = "from config import MODEL_NAME, SAFETY_SETTINGS\n" + content

    # 2. Replace hardcoded model_name with config variable
    # Regex looks for: model_name='gemini-...' or "gemini-..."
    content = re.sub(
        r"model_name=['\"]gemini-.*?['\"]", 
        "model_name=MODEL_NAME", 
        content
    )

    # 3. Replace hardcoded safety_settings with config variable
    # This matches the list structure roughly
    content = re.sub(
        r"safety_settings=\[\s*\{.*?\}\s*\]", 
        "safety_settings=SAFETY_SETTINGS", 
        content, 
        flags=re.DOTALL
    )

    with open(filepath, "w") as f:
        f.write(content)
    print(f"✅ Optimized: {filepath}")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    for d in DIRECTORIES:
        dir_path = os.path.join(base_dir, d)
        if not os.path.exists(dir_path):
            continue
            
        for filename in os.listdir(dir_path):
            if filename.endswith(".py") and filename != "__init__.py":
                optimize_file(os.path.join(dir_path, filename))

    print("\n🚀 All agents upgraded to use 'config.MODEL_NAME'.")

if __name__ == "__main__":
    main()