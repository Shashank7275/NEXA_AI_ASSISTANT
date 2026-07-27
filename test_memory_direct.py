#!/usr/bin/env python
"""
Direct test of memory system — simulates what Jarvis should do
when user asks "याद है?" or similar questions.
"""
import asyncio
from memory.jarvis_memory import get_recent_conversations

async def main():
    print("=" * 60)
    print("MEMORY SYSTEM TEST - Simulating Jarvis Response")
    print("=" * 60)
    print()
    
    # Simulate user asking for past conversation
    user_input = "याद है? मैंने पहले क्या बोला था?"
    print(f"User: {user_input}")
    print()
    
    # Check if memory keywords are present
    memory_keywords = ["याद है", "पहले क्या", "बात हुई", "पिछली", "history", "memory", "पुरानी बातें"]
    has_memory_keyword = any(kw in user_input for kw in memory_keywords)
    
    if has_memory_keyword:
        print("✓ Memory retrieval keyword detected!")
        print("✓ Calling get_recent_conversations()...")
        print()
        
        # Call the memory retrieval tool
        result = await get_recent_conversations(10)
        
        # Jarvis would then respond with this:
        print("Jarvis Response:")
        print("-" * 60)
        print(f"Sir, आपकी याद है? जी, मुझे सब याद है। आपकी पिछली बातचीत:\n\n{result}")
        print("-" * 60)
    else:
        print("✗ No memory keyword found")

if __name__ == "__main__":
    asyncio.run(main())
