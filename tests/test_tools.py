import pytest
import os
import shutil
from tools.file_tool import FileTool
from tools.run_code import run_python_code

TEST_DIR = "test_data"

@pytest.fixture(scope="module")
def setup_teardown():
    if not os.path.exists(TEST_DIR):
        os.makedirs(TEST_DIR)
    yield
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)

def test_file_tool_write_and_read(setup_teardown):
    """Tests writing to and reading from a file."""
    filepath = os.path.join(TEST_DIR, "test_file.txt")
    content = "Hello CoderLang"
    
    # Write
    result = FileTool.write_file(filepath, content)
    assert "Successfully wrote" in result
    
    # Read
    read_content = FileTool.read_file(filepath)
    assert read_content == content

def test_run_code_success():
    """Tests successful Python code execution."""
    code = "print('Hello World')"
    result = run_python_code(code)
    
    assert result['return_code'] == 0
    assert result['stdout'].strip() == "Hello World"
    assert result['stderr'] == ""

def test_run_code_error():
    """Tests Python code execution with errors."""
    code = "print(1/0)" # Division by zero
    result = run_python_code(code)
    
    assert result['return_code'] != 0
    assert "ZeroDivisionError" in result['stderr']