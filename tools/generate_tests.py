import os
import logging
import subprocess
import tempfile
import json
import re

log = logging.getLogger(__name__)

class TestTool:
    """
    A specialized tool for managing and executing generated tests.
    Unlike simple code execution, this uses 'pytest' to provide 
    structured pass/fail reports.
    """

    def __init__(self, test_dir="tests/generated"):
        self.test_dir = test_dir
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)

    def save_test_file(self, code_string: str, filename: str = "test_generated.py") -> str:
        """Saves the generated test code to a file."""
        file_path = os.path.join(self.test_dir, filename)
        try:
            with open(file_path, "w") as f:
                f.write(code_string)
            log.info(f"Saved generated tests to {file_path}")
            return file_path
        except Exception as e:
            log.error(f"Failed to save test file: {e}")
            return ""

    def run_pytest(self, file_path: str) -> dict:
        """
        Runs pytest on a specific file and returns a structured summary.
        """
        log.info(f"Running pytest on {file_path}...")
        
        if not os.path.exists(file_path):
            return {"error": "Test file not found", "passed": False}

        try:
            # Run pytest as a subprocess
            # -q: quiet
            # --tb=short: shorter traceback
            cmd = ["pytest", "-q", "--tb=short", file_path]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=15
            )
            
            output = result.stdout + result.stderr
            
            # Parse the output for summary (e.g., "2 passed, 1 failed")
            passed = result.returncode == 0
            
            summary_match = re.search(r'([\d]+) passed', output)
            pass_count = int(summary_match.group(1)) if summary_match else 0
            
            fail_match = re.search(r'([\d]+) failed', output)
            fail_count = int(fail_match.group(1)) if fail_match else 0

            log.info(f"Pytest finished. Passed: {pass_count}, Failed: {fail_count}")

            return {
                "passed": passed,
                "summary": f"Passed: {pass_count}, Failed: {fail_count}",
                "output": output,
                "return_code": result.returncode
            }

        except subprocess.TimeoutExpired:
            return {"error": "Test execution timed out", "passed": False}
        except Exception as e:
            return {"error": str(e), "passed": False}