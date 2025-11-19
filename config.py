import os

# --- MODEL TIERS ---
FAST_MODEL = "gemini-1.5-flash"    # For Speed & Routing
SMART_MODEL = "gemini-2.5-pro"     # For Complex Reasoning

# Default fallback
MODEL_NAME = FAST_MODEL 

# --- SAFETY SETTINGS ---
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]