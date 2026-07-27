import os
from datetime import datetime

try:
    import pyautogui
except Exception:
    pyautogui = None

from livekit.agents import function_tool


@function_tool
async def screenshot_tool(save_dir: str = None) -> dict:
    """LiveKit function tool to take a screenshot and save it to a screenshots folder.
    Returns a dict: {'success': True, 'path': path} or {'success': False, 'error': msg}
    """
    save_dir = save_dir or os.path.join(os.path.dirname(__file__), "screenshots")
    try:
        os.makedirs(save_dir, exist_ok=True)
        filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        path = os.path.join(save_dir, filename)
        if pyautogui is None:
            return {"success": False, "error": "pyautogui not installed"}
        img = pyautogui.screenshot()
        img.save(path)
        try:
            # write latest screenshot path for GUI to pick up
            latest_file = os.path.join(save_dir, "latest_screenshot.txt")
            with open(latest_file, "w", encoding="utf-8") as f:
                f.write(path)
        except Exception:
            pass
        return {"success": True, "path": path}
    except Exception as e:
        return {"success": False, "error": str(e)}
