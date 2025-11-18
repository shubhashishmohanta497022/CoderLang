import json
import os
import logging

log = logging.getLogger(__name__)

class MemoryStore:
    def __init__(self, memory_dir="memory"):
        self.memory_dir = memory_dir
        self.short_term_path = os.path.join(memory_dir, "short_term.json")
        self.long_term_path = os.path.join(memory_dir, "long_term.json")
        
        if not os.path.exists(self.memory_dir):
            os.makedirs(self.memory_dir)

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