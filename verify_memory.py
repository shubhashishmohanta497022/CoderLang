from memory.memory_store import MemoryStore
import time
import os

def verify_memory():
    print("🚀 Starting MemoryStore Verification...")
    
    # Initialize
    memory = MemoryStore(memory_dir="test_memory")
    print("✅ MemoryStore initialized.")
    
    # 1. Create Chat Session
    session_id_1 = memory.create_chat_session(title="Test Chat 1")
    print(f"✅ Created Session 1: {session_id_1}")
    
    # 2. Save Messages
    memory.save_message(session_id_1, "user", "Hello, world!")
    memory.save_message(session_id_1, "assistant", "Hello! How can I help?")
    print("✅ Saved messages to Session 1.")
    
    # 3. Load History
    history = memory.load_chat_history(session_id_1)
    assert len(history) == 2
    assert history[0]["content"] == "Hello, world!"
    assert history[1]["content"] == "Hello! How can I help?"
    print("✅ Loaded history correctly.")
    
    # 4. Create Another Session
    time.sleep(1) # Ensure timestamp difference
    session_id_2 = memory.create_chat_session(title="Test Chat 2")
    print(f"✅ Created Session 2: {session_id_2}")
    
    # 5. List Sessions
    sessions = memory.list_chat_sessions()
    assert len(sessions) == 2
    # Should be sorted by updated_at desc (Session 2 created last)
    assert sessions[0]["id"] == session_id_2
    print("✅ Listed sessions correctly (sorted).")
    
    # 6. Auto-title Update
    session_id_3 = memory.create_chat_session() # Default title "New Chat"
    memory.save_message(session_id_3, "user", "This is a long message that should become the title.")
    sessions = memory.list_chat_sessions()
    # Find session 3
    s3 = next(s for s in sessions if s["id"] == session_id_3)
    assert s3["title"] != "New Chat"
    print(f"✅ Auto-title updated: {s3['title']}")
    
    # Cleanup
    import shutil
    shutil.rmtree("test_memory")
    print("✅ Cleanup complete.")
    
    print("\n🎉 All Memory Tests Passed!")

if __name__ == "__main__":
    verify_memory()
