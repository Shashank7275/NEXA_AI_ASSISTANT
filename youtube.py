import subprocess
import webbrowser
import os
import threading
import time
import asyncio
import yt_dlp
import pyautogui
import pyperclip
from pathlib import Path
from livekit.agents import function_tool

class JarvisMediaController:
    def __init__(self, download_folder=None):
        if download_folder is None:
            base_dir = Path.home()
            music_dir = base_dir / "Music"
            self.download_folder = music_dir / "JarvisDownloads"
        else:
            self.download_folder = Path(download_folder)
        self.download_folder.mkdir(parents=True, exist_ok=True)
        self.youtube_url = "https://www.youtube.com/watch?si=ZMwl-IuuX73YT-vx&v=Qhwafoo7Pnc&feature=youtu.be"
        print(f"🎵 Jarvis Media Controller initialized. Downloads: {self.download_folder}")

    def play_youtube(self, mode="big"):
        if mode == "small":
            url = f"{self.youtube_url}&autoplay=1"
        else:
            url = f"{self.youtube_url}&autoplay=1&disablekb=1"
        chrome_exe = Path("C:/Program Files/Google/Chrome/Application/chrome.exe")
        try:
            if chrome_exe.exists():
                subprocess.Popen([str(chrome_exe), "--new-window", "--start-maximized", url])
            else:
                webbrowser.open(url)
        except Exception:
            webbrowser.open(url)
        print(f"🎥 Playing YouTube song in {mode} screen mode")

    def download_song(self):
        """Download YouTube song as high quality MP3"""
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{self.download_folder}/%(title)s.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '0',
                }],
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.youtube_url])
            
            print(f"✅ Song downloaded to: {self.download_folder}")
        except Exception as e:
            print(f"❌ Download error: {str(e)}")

    def share_whatsapp(self, contact_name="Friend"):
        """Share song link on WhatsApp"""
        message = f"🎵 Check out this awesome song! {self.youtube_url}"
        
        # Open WhatsApp Web search
        webbrowser.open('https://web.whatsapp.com/')
        time.sleep(3)  # Wait for load
        
        # Copy message to clipboard
        pyperclip.copy(message)
        
        print(f"📱 WhatsApp opened. Paste message to '{contact_name}' and press Enter.")
        print("💡 Manual step: Search contact, Ctrl+V, Enter")
        
        # Optional: Auto-send simulation (uncomment if calibrated)
        # time.sleep(5)
        # pyautogui.hotkey('ctrl', 'v')
        # pyautogui.press('enter')

    def parse_command(self, command):
        """Parse voice commands"""
        command = command.lower()
        
        play_keywords = [
            'play song',
            'play music',
            'play youtube',
            'play my favourite song',
            'play my favorite song',
        ]
        favourite_keywords = [
            'my favourite song',
            'my favorite song',
            'favourite song',
            'favorite song',
        ]
        
        if (
            any(word in command for word in play_keywords)
            or any(word in command for word in favourite_keywords)
            or ('play' in command and ('song' in command or 'music' in command))
        ):
            mode = "big" if any(word in command for word in ['big', 'large', 'full', 'theatre', 'theater']) else "small"
            return ('play', mode)
        
        elif (
            'download song' in command
            or 'save song' in command
            or ('download' in command and ('song' in command or 'music' in command or 'video' in command))
        ):
            return ('download', None)
        
        elif (
            any(word in command for word in ['share whatsapp', 'send whatsapp'])
            or ('whatsapp' in command and ('share' in command or 'send' in command or 'video' in command or 'song' in command))
        ):
            return ('share', None)
        
        return None

    def execute(self, voice_command):
        """Main execution from voice command"""
        action = self.parse_command(voice_command)
        if not action:
            print("❌ Unknown command. Try: 'play song', 'play big screen', 'download song', 'share whatsapp'")
            return
        
        action_type, param = action
        
        if action_type == 'play':
            self.play_youtube(param)
        elif action_type == 'download':
            self.download_song()
        elif action_type == 'share':
            self.share_whatsapp()


media_controller = JarvisMediaController()


@function_tool
async def play_song(mode: str = "big"):
    """
    Play Sir Shashank's favourite YouTube song.
    
    Args:
        mode: "big" for maximized screen, "small" for mini player.
    """
    if mode not in ("big", "small"):
        mode = "big"
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, media_controller.play_youtube, mode)
    return f"Favourite song playing in {mode} screen mode."


@function_tool
async def download_favourite_song():
    """
    Download Sir Shashank's favourite YouTube song as high quality audio.
    """
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, media_controller.download_song)
    return f"Favourite song downloaded to: {media_controller.download_folder}"


@function_tool
async def share_favourite_song_whatsapp(contact_name: str = "Friend"):
    """
    Open WhatsApp Web ready to share favourite song link.
    
    Args:
        contact_name: Name hint for the contact you will send to.
    """
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, media_controller.share_whatsapp, contact_name)
    return f"WhatsApp Web opened to share favourite song with {contact_name}."

# ========== INTEGRATION WITH YOUR JARVIS ==========
def main():
    jarvis_media = JarvisMediaController()
    
    # Test commands
    test_commands = [
        "play song big screen",
        "play song small screen", 
        "download song",
        "share whatsapp"
    ]
    
    print("🎵 Jarvis Media Demo:")
    for cmd in test_commands:
        print(f"\nCommand: {cmd}")
        jarvis_media.execute(cmd)
        time.sleep(3)

# Add to your main Jarvis voice loop:
"""
jarvis_media = JarvisMediaController()
if any(word in voice_text.lower() for word in ['song', 'music', 'youtube', 'play']):
    jarvis_media.execute(voice_text)
"""

if __name__ == "__main__":
    main()
