import pytest
import os
import json
import shutil
from memory.memory_store import MemoryStore

TEST_MEM_DIR = "test_memory"

@pytest.fixture
def memory_store():
    # Setup
    if os.path.exists(TEST_MEM_DIR):
        shutil.rmtree(TEST_MEM_DIR)
    
    store = MemoryStore(memory_dir=TEST_MEM_DIR)
    yield store
    
    # Teardown
    if os.path.exists(TEST_MEM_DIR):
        shutil.rmtree(TEST_MEM_DIR)

def test_short_term_memory(memory_store):
    """Tests putting and getting short term memory."""
    memory_store.put("user_goal", "build website")
    retrieved = memory_store.get("user_goal")
    assert retrieved == "build website"

def test_long_term_memory(memory_store):
    """Tests putting and getting long term memory."""
    memory_store.put("preferred_language", "Python", memory_type="long")
    retrieved = memory_store.get("preferred_language", memory_type="long")
    assert retrieved == "Python"

def test_persistence(memory_store):
    """Tests that data persists in the JSON file."""
    memory_store.put("persisted_key", "value123")
    
    # Manually check file
    with open(os.path.join(TEST_MEM_DIR, "short_term.json"), 'r') as f:
        data = json.load(f)
        assert data["persisted_key"] == "value123"