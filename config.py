import os

# --- MODEL TIERS ---

# 1. FAST MODEL: Used for Router, Planner, and simple tasks.
# We use the stable 2.5 Flash as seen in your list.
FAST_MODEL = "gemini-2.5-flash"    

# 2. SMART MODEL: Used for Coding, Debugging, and Explanation.
# We use the specialized Gemini 3 Pro Preview you found.
SMART_MODEL = "gemini-3-pro-preview"     

# Default fallback
MODEL_NAME = FAST_MODEL 

# --- SAFETY SETTINGS ---
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]