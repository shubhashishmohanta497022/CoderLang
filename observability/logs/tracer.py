import json
import os
import time

# Define the trace file path
TRACE_FILE = os.path.join(os.path.dirname(__file__), 'traces', 'traces.json')
TRACE_DIR = os.path.join(os.path.dirname(__file__), 'traces')

# Ensure the trace directory exists
if not os.path.exists(TRACE_DIR):
    os.makedirs(TRACE_DIR)

class Tracer:
    """
    Tracks and records the flow of execution between agents and tools.
    This provides a trace/timeline of the CoderLang session.
    """
    def __init__(self, session_id: str = None):
        self.session_id = session_id if session_id else f"session-{int(time.time())}"
        self.trace = []

    def record_event(self, source_agent: str, target_agent: str, action: str, details: dict = None):
        """
        Records a single step in the agent collaboration process.
        
        Args:
            source_agent: The agent or module initiating the action (e.g., 'Orchestrator').
            target_agent: The agent or tool being called (e.g., 'CodingAgent', 'run_code').
            action: A brief description of the action (e.g., 'REQUEST_CODE', 'TEST_RUN', 'DEBUG_FIX').
            details: Optional dictionary for additional context (e.g., error message).
        """
        event = {
            "timestamp": time.time(),
            "source": source_agent,
            "target": target_agent,
            "action": action,
            "details": details if details is not None else {}
        }
        self.trace.append(event)

    def save_trace(self):
        """Saves the current session trace to a file."""
        try:
            # We don't want to overwrite the main TRACE_FILE; save it to a session-specific name
            filename = os.path.join(TRACE_DIR, f"{self.session_id}.json")
            with open(filename, 'w') as f:
                json.dump(self.trace, f, indent=2)
            print(f"Trace saved for session {self.session_id} to {filename}")
        except Exception as e:
            print(f"Error saving trace: {e}")
            
    def show_trace(self) -> str:
        """Formats the trace events into a readable string timeline."""
        output = [f"--- Trace for Session: {self.session_id} ---"]
        for i, event in enumerate(self.trace):
            detail_snippet = f"({event['details'].get('status', event['details'].get('error', 'OK'))})"
            
            output.append(
                f"[{i+1:02d}] {event['source']:<15} -> {event['target']:<15} : {event['action']:<20} {detail_snippet}"
            )
        return "\n".join(output)

# Placeholder: You would instantiate this in coordinator.py's __init__
# self.tracer = Tracer()
# And record steps in execute_plan:
# self.tracer.record_event("Orchestrator", agent_name, "AGENT_START")