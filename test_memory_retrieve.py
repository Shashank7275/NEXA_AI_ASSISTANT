#!/usr/bin/env python
import asyncio
from memory.jarvis_memory import _get_recent_entries_sync, get_recent_conversations

# Test sync retrieval
print('=== Testing sync retrieval ===')
entries = _get_recent_entries_sync(10)
print(f'Entries found: {len(entries)}')
for e in entries:
    print(f'  - {e.get("speaker")}: {e.get("text")}')

# Test async tool
print('\n=== Testing async tool ===')
async def test():
    result = await get_recent_conversations(10)
    print(f'Tool result:\n{result}')

asyncio.run(test())
