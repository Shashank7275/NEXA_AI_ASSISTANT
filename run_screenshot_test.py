import asyncio
import os
import sys

from pprint import pprint

print('Python executable:', sys.executable)
print('CWD:', os.getcwd())

try:
    from Jarvis_screenshot import screenshot_tool
except Exception as e:
    print('Import error:', e)
    raise

async def main():
    print('Calling screenshot_tool...')
    try:
        res = await screenshot_tool()
        pprint(res)
    except Exception as e:
        print('Error while running screenshot_tool:', e)

if __name__ == '__main__':
    asyncio.run(main())
