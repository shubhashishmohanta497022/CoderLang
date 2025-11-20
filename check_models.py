import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Configure the API
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    print("Error: GOOGLE_API_KEY not found in environment variables.")
else:
    genai.configure(api_key=api_key)

    print("Checking available models...")
    try:
        # List all models available to your API key
        for m in genai.list_models():
            # Only show models that support content generation (chat/text)
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
    except Exception as e:
        print(f"Error listing models: {e}")