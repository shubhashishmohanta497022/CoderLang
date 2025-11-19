import json
import time
import os
import logging
from typing import Dict, Any

log = logging.getLogger(__name__)

METRICS_FILE = os.path.join(os.path.dirname(__file__), 'metrics.json')

class MetricsTracker:
    def __init__(self):
        self.metrics_file = METRICS_FILE
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.metrics_file):
            with open(self.metrics_file, 'w') as f:
                json.dump({
                    "total_requests": 0,
                    "successful_requests": 0,
                    "failed_requests": 0,
                    "total_latency": 0.0,
                    "agent_usage": {}
                }, f)

    def _load(self) -> Dict[str, Any]:
        try:
            with open(self.metrics_file, 'r') as f:
                return json.load(f)
        except Exception:
            return {}

    def _save(self, data: Dict[str, Any]):
        try:
            with open(self.metrics_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            log.error(f"Failed to save metrics: {e}")

    def record_request(self, duration: float, success: bool):
        data = self._load()
        data["total_requests"] = data.get("total_requests", 0) + 1
        
        if success:
            data["successful_requests"] = data.get("successful_requests", 0) + 1
        else:
            data["failed_requests"] = data.get("failed_requests", 0) + 1
            
        data["total_latency"] = data.get("total_latency", 0.0) + duration
        self._save(data)

    def record_agent_usage(self, agent_name: str):
        data = self._load()
        usage = data.get("agent_usage", {})
        usage[agent_name] = usage.get(agent_name, 0) + 1
        data["agent_usage"] = usage
        self._save(data)

    def get_summary(self):
        data = self._load()
        total = data.get("total_requests", 1)
        avg_latency = data.get("total_latency", 0) / total if total > 0 else 0
        return {
            "Total Requests": total,
            "Success Rate": f"{(data.get('successful_requests', 0) / total) * 100:.1f}%",
            "Avg Latency": f"{avg_latency:.2f}s"
        }