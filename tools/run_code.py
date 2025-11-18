import subprocess
import logging
import tempfile
import os

log = logging.getLogger(__name__)

def run_python_code(code_string: str) -> dict:
    """
    Executes a string of Python code in a sandboxed subprocess.
    
    Args:
        code_string: The Python code to execute.
        
    Returns:
        A dictionary containing:
        - 'stdout' (str): The standard output.
        - 'stderr' (str): The standard error (or None if no error).
        - 'return_code' (int): The exit code of the process.
    """
    log.info("Received request to execute code.")
    
    # We use a temporary file to write the code and execute it.
    # This is more robust than passing a long string to the CLI.
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
        temp_file.write(code_string)
        temp_path = temp_file.name

    log.info(f"Code written to temporary file: {temp_path}")
    
    try:
        # Execute the temporary file using 'python'
        # We set a timeout (e.g., 10 seconds) for safety.
        result = subprocess.run(
            ['python', temp_path],
            capture_output=True,
            text=True,
            timeout=10  # Safety: prevent long-running/infinite loops
        )
        
        stdout = result.stdout
        stderr = result.stderr
        return_code = result.returncode

        log.info(f"Code execution finished with return code: {return_code}")
        if stdout:
            log.info(f"STDOUT: {stdout[:200]}...") # Log snippet
        if stderr:
            log.warning(f"STDERR: {stderr[:200]}...") # Log snippet
            
        return {
            "stdout": stdout,
            "stderr": stderr,
            "return_code": return_code
        }

    except subprocess.TimeoutExpired:
        log.error("Code execution TIMED OUT.")
        return {
            "stdout": "",
            "stderr": "Error: Code execution timed out after 10 seconds.",
            "return_code": 1
        }
    except Exception as e:
        log.error(f"An unexpected error occurred during execution: {e}")
        return {
            "stdout": "",
            "stderr": f"An unexpected error occurred: {e}",
            "return_code": 1
        }
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)
            log.info(f"Temporary file {temp_path} cleaned up.")