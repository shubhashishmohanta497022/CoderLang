import json
import os
import logging
import uuid
import time
from datetime import datetime

log = logging.getLogger(__name__)

class MemoryStore:
    def __init__(self, memory_dir="memory"):
        self.memory_dir = memory_dir
        self.short_term_path = os.path.join(memory_dir, "short_term.json")
        self.long_term_path = os.path.join(memory_dir, "long_term.json")
        self.chats_dir = os.path.join(memory_dir, "chats")
        
        if not os.path.exists(self.memory_dir):
            os.makedirs(self.memory_dir)
            
        if not os.path.exists(self.chats_dir):
            os.makedirs(self.chats_dir)

        self._init_file(self.short_term_path)
        self._init_file(self.long_term_path)
        
    def _init_file(self, filepath):
        if not os.path.exists(filepath):
            with open(filepath, 'w') as f:
                json.dump({}, f)

    def _load(self, filepath):
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception:
            return {}

    def _save(self, filepath, data):
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            log.error(f"Failed to save memory: {e}")

    def get(self, key, memory_type="short"):
        path = self.long_term_path if memory_type == "long" else self.short_term_path
        return self._load(path).get(key)

    def put(self, key, value, memory_type="short"):
        path = self.long_term_path if memory_type == "long" else self.short_term_path
        data = self._load(path)
        data[key] = value
        self._save(path, data)

    def get_all_context(self):
        long_term = self._load(self.long_term_path)
        short_term = self._load(self.short_term_path)
        
        context_str = ""
        if long_term:
            context_str += "User Preferences (Long Term Memory):\n"
            for k, v in long_term.items():
                context_str += f"- {k}: {v}\n"
        
        if short_term:
            context_str += "\nCurrent Session Context (Short Term Memory):\n"
            for k, v in short_term.items():
                context_str += f"- {k}: {v}\n"
                
        return context_str

    # --- Chat Session Management ---

    def create_chat_session(self, title="New Chat"):
        session_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        chat_data = {
            "id": session_id,
            "title": title,
            "created_at": timestamp,
            "updated_at": timestamp,
            "messages": []
        }
        filepath = os.path.join(self.chats_dir, f"{session_id}.json")
        self._save(filepath, chat_data)
        return session_id

    def save_message(self, session_id, role, content, metadata=None):
        filepath = os.path.join(self.chats_dir, f"{session_id}.json")
        if not os.path.exists(filepath):
            log.error(f"Chat session {session_id} not found.")
            return

        chat_data = self._load(filepath)
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        chat_data["messages"].append(message)
        chat_data["updated_at"] = datetime.now().isoformat()
        
        # Auto-update title if it's the first user message and title is default
        if role == "user" and len(chat_data["messages"]) == 1 and chat_data["title"] == "New Chat":
            chat_data["title"] = content[:30] + "..." if len(content) > 30 else content
            
        self._save(filepath, chat_data)

    def load_chat_history(self, session_id):
        filepath = os.path.join(self.chats_dir, f"{session_id}.json")
        if not os.path.exists(filepath):
            return []
        chat_data = self._load(filepath)
        return chat_data.get("messages", [])

    def list_chat_sessions(self):
        sessions = []
        if not os.path.exists(self.chats_dir):
            return []
            
        for filename in os.listdir(self.chats_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self.chats_dir, filename)
                chat_data = self._load(filepath)
                if chat_data:
                    sessions.append({
                        "id": chat_data.get("id"),
                        "title": chat_data.get("title", "Untitled"),
                        "updated_at": chat_data.get("updated_at", "")
                    })
        
        # Sort by updated_at descending
        sessions.sort(key=lambda x: x["updated_at"], reverse=True)
        return sessions

    def delete_chat_session(self, session_id):
        filepath = os.path.join(self.chats_dir, f"{session_id}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False

    # --- Import / Export ---

    def export_chat_session(self, session_id):
        """Returns the JSON string of a chat session."""
        filepath = os.path.join(self.chats_dir, f"{session_id}.json")
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return f.read()
        return None

    def import_chat_session(self, json_data):
        """Imports a chat session from a JSON string or dict."""
        try:
            if isinstance(json_data, str):
                data = json.loads(json_data)
            else:
                data = json_data
            
            # Basic validation
            if "id" not in data or "messages" not in data:
                return False, "Invalid chat format: Missing 'id' or 'messages'"
            
            # Ensure ID doesn't conflict (or overwrite if intended? Let's overwrite for restore)
            # If we wanted to avoid overwrite, we'd generate a new ID.
            # For now, let's keep the ID to allow exact restoration.
            
            filepath = os.path.join(self.chats_dir, f"{data['id']}.json")
            self._save(filepath, data)
            return True, f"Chat '{data.get('title', 'Untitled')}' imported successfully."
        except Exception as e:
            return False, str(e)

    def get_full_memory_dump(self):
        """Returns a dictionary containing all memory (Short, Long, Chats)."""
        dump = {
            "short_term": self._load(self.short_term_path),
            "long_term": self._load(self.long_term_path),
            "chats": []
        }
        
        if os.path.exists(self.chats_dir):
            for filename in os.listdir(self.chats_dir):
                if filename.endswith(".json"):
                    filepath = os.path.join(self.chats_dir, filename)
                    dump["chats"].append(self._load(filepath))
        
        return dump