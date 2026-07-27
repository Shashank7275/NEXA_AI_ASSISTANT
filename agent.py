from dotenv import load_dotenv

import os
import sys
import asyncio
import subprocess
import logging
import re

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    google,
    noise_cancellation,
)
from NEXA_prompts import behavior_prompts, Reply_prompts
from NEXA_screenshot import screenshot_tool
from NEXA_google_search import google_search, get_current_datetime
from memory.jarvis_memory import load_memory, save_memory, get_recent_conversations, add_memory_entry
from memory_interceptor import MEMORY_KEYWORDS
from NEXA_get_whether import get_weather
from NEXA_window_CTRL import open, close, folder_file
from NEXA_file_open import Play_file
from keyboard_mouse_CTRL import move_cursor_tool, mouse_click_tool, scroll_cursor_tool, type_text_tool, press_key_tool, swipe_gesture_tool, press_hotkey_tool, control_volume_tool
from flipkart import flipkart_buy_cod, flipkart_buy_cod_auto, flipkart_buy_auto
from ip_address import get_ip_info
from youtube import play_song, download_favourite_song, share_favourite_song_whatsapp

from image_to_pdf import image_to_pdf
from image_generate import generate_image_tool

from object_detection import detect_objects

from file_search import jarvis_file_search_command
from thinking import JarvisAutoThinking


load_dotenv()
if not os.getenv("GOOGLE_API_KEY"):
    base_dir = os.path.dirname(__file__)
    try:
        if getattr(sys, "frozen", False):
            base_dir = os.path.dirname(sys.executable)
    except Exception:
        pass
    for p in [os.path.join(base_dir, ".env"), os.path.join(os.path.dirname(base_dir), ".env")]:
        try:
            if os.path.exists(p):
                load_dotenv(p)
                break
        except Exception:
            pass
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ENABLE_MEMORY_INTERCEPTOR = False


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=behavior_prompts,
                         tools=[
                            google_search,
                            get_current_datetime,
                            get_weather,
                            open, 
                            close, 
                            load_memory, save_memory,
                            get_recent_conversations, 
                            add_memory_entry, 
                            folder_file,
                            Play_file,  
                            screenshot_tool, 
                            move_cursor_tool,
                            mouse_click_tool, 
                            scroll_cursor_tool, 
                            type_text_tool, 
                            press_key_tool, 
                            press_hotkey_tool, 
                            control_volume_tool, #
                            swipe_gesture_tool,
                            image_to_pdf,
                            generate_image_tool,
                            detect_objects,
                            flipkart_buy_cod,
                            flipkart_buy_cod_auto,
                            flipkart_buy_auto,
                           
                            get_ip_info,
                            play_song,
                            download_favourite_song,
                            share_favourite_song_whatsapp,
                           
                            jarvis_file_search_command,
                            
                         ]
                         )


async def entrypoint(ctx: agents.JobContext):
    """Entry point for LiveKit agent session with improved error handling"""
    max_retries = 5  # Increased from 3
    retry_count = 0
    base_wait_time = 3  # Increased from 2
    
    auto_thinker = JarvisAutoThinking()
    print("🧠 JarvisAutoThinking background assistant started")
    
    while retry_count < max_retries:
        try:
            print(f"\n🚀 Starting agent session (attempt {retry_count + 1}/{max_retries})...")
            
            session = AgentSession(
                llm=google.beta.realtime.RealtimeModel(
                    voice="Leda"
                )
            )
            
            await session.start(
                room=ctx.room,
                agent=Assistant(),
                room_input_options=RoomInputOptions(
                    noise_cancellation=noise_cancellation.BVC(),
                    video_enabled=False 
                ),
            )

            await ctx.connect()
            print("✅ Connected to room, waiting for audio input...")

            # Generate reply with timeout handling
            try:
                # Try to inject memory context into the reply instructions
                instructions = Reply_prompts
                
                if ENABLE_MEMORY_INTERCEPTOR:
                    try:
                        print("🧠 Fetching memory context...")
                        # Fetch recent conversations to inject context
                        memory_context = await get_recent_conversations(limit=5)  # Reduced from 10
                        
                        # Only inject if there's actual memory, keep it brief
                        if "अभी तक कोई बातचीत याद नहीं है" not in memory_context:
                            instructions = f"""{Reply_prompts}

[RECENT CONTEXT]
{memory_context}
[/CONTEXT]"""
                            print("✅ Memory context injected")
                        else:
                            instructions = Reply_prompts
                            print("ℹ️ No previous conversations to inject")
                    except Exception as e:
                        print(f"⚠️ Memory injection skipped: {e}")
                        instructions = Reply_prompts
                
                print("📡 Sending instructions to LLM (this may take a moment)...")
                await session.generate_reply(
                    instructions=instructions
                )
                print("✅ Session completed successfully")
                break  # Success - exit retry loop
                
            except Exception as e:
                error_msg = str(e).lower()
                print(f"⚠️ Reply generation error (attempt {retry_count + 1}/{max_retries}): {e}")
                
                # Check if it's a timeout/connection error worth retrying
                if any(keyword in error_msg for keyword in ["timed out", "timeout", "connection", "websocket", "closed"]):
                    if retry_count < max_retries - 1:
                        retry_count += 1
                        wait_time = base_wait_time * retry_count  # Exponential backoff
                        print(f"🔄 Connection issue detected. Retrying in {wait_time}s... ({retry_count}/{max_retries})")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        print("❌ Max retries exceeded after multiple timeouts")
                        raise
                else:
                    # Not a timeout - propagate error immediately
                    raise
            
        except KeyboardInterrupt:
            print("\n⛔ Agent stopped by user")
            break
        except Exception as e:
            print(f"❌ Session error (attempt {retry_count + 1}/{max_retries}): {e}")
            retry_count += 1
            
            if retry_count < max_retries:
                wait_time = base_wait_time * retry_count  # Exponential backoff
                print(f"⏳ Waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)
            else:
                print("❌ Max retries exceeded. Shutting down.")
                raise


if __name__ == "__main__":
    # Try to start the GUI alongside the agent (runs in a separate process)
    try:
        gui_path = os.path.join(os.path.dirname(__file__), "NEXA_gui.py")
        if os.path.exists(gui_path):
            # Start GUI as a detached subprocess so the agent can continue
            subprocess.Popen([sys.executable, gui_path], stdout=None, stderr=None, stdin=None, close_fds=True)
        else:
            print("jarvis_gui.py not found; GUI will not be started.")
    except Exception as e:
        print("Failed to start GUI subprocess:", e)

    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
