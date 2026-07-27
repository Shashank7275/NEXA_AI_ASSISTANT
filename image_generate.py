import os
import asyncio
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import pyttsx3
import requests
import io
from huggingface_hub import InferenceClient
from livekit.agents import function_tool

# Config
OUT_DIR = Path("jarvis_images")
OUT_DIR.mkdir(exist_ok=True)
HF_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"
HF_TOKEN = os.getenv("HF_TOKEN")
client = InferenceClient(model=HF_MODEL, token=HF_TOKEN) if HF_TOKEN else InferenceClient(model=HF_MODEL)

engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id if len(voices) > 1 else voices[0].id)  # Female voice if available

async def speak(text):
    """Jarvis TTS"""
    engine.say(text)
    engine.runAndWait()

async def generate_image(prompt, width=1024, height=1024, steps=20, guidance=7.5):
    """
    Generate advanced AI image from text command.
    Fast: 20 steps for ~10s gen time.
    """
    try:
        await speak(f"Generating {prompt}... Stand by.")
        image = client.text_to_image(
            prompt=prompt,
            height=height,
            width=width,
            num_inference_steps=steps,
            guidance_scale=guidance,
            negative_prompt="blurry, low quality, deformed, ugly"
        )
        return image
    except Exception as e:
        await speak("Generation failed. Rate limit or network issue.")
        raise e

def save_and_open(image: Image.Image, prompt: str):
    """Save with timestamp, preview in GUI, open in default viewer."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"jarvis_{prompt.replace(' ', '_')[:50]}_{timestamp}.png"
    path = OUT_DIR / filename
    image.save(path)
    
    # GUI preview
    root = tk.Tk()
    root.title(f"Jarvis Generated: {prompt[:30]}")
    photo = ImageTk.PhotoImage(image.resize((512, 512)))
    label = tk.Label(root, image=photo)
    label.pack()
    tk.Button(root, text="Open Full", command=lambda: os.startfile(path)).pack()
    root.mainloop()
    
    os.startfile(path)
    return str(path)

async def jarvis_generate_command(prompt: str):
    """Main Jarvis command handler."""
    try:
        image = await generate_image(prompt)
        path = save_and_open(image, prompt)
        await speak(f"Image generated and opened: {path}")
        return f"✅ Generated: {path}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

@function_tool
async def generate_image_tool(prompt: str, width: int = 1024, height: int = 1024, steps: int = 20, guidance: float = 7.5):
    """
    LiveKit tool wrapper: generates an image and returns the saved path.
    """
    image = await generate_image(prompt, width=width, height=height, steps=steps, guidance=guidance)
    path = save_and_open(image, prompt)
    await speak(f"Image generated and opened: {path}")
    return f"{path}"

# GUI/Voice Entry Point
def run_gui():
    root = tk.Tk()
    root.title("Jarvis Image Generator")
    root.geometry("400x200")
    
    tk.Label(root, text="Enter prompt:").pack(pady=10)
    prompt_entry = tk.Entry(root, width=50)
    prompt_entry.pack(pady=5)
    prompt_entry.insert(0, "futuristic jarvis ai interface")
    
    async def generate():
        result = await jarvis_generate_command(prompt_entry.get())
        messagebox.showinfo("Jarvis", result)
    
    tk.Button(root, text="Generate Image", command=lambda: asyncio.run(generate())).pack(pady=10)
    root.mainloop()

# Voice/Command Integration Example (import in main.py)
# asyncio.run(jarvis_generate_command("cyberpunk city at night"))

if __name__ == "__main__":
    print("🚀 Jarvis Advanced Image Generator Active")
    print("Run: python generate.py")
    print("Or integrate: from generate import jarvis_generate_command")
    run_gui()
