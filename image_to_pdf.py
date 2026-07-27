import asyncio
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from PIL import Image
import pyttsx3  # pip install pyttsx3 (your Jarvis TTS)

from livekit.agents import function_tool

def speak(text):
    """Jarvis TTS - your standard voice feedback."""
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)  # Female voice (your pref)
    engine.say(text)
    engine.runAndWait()

@function_tool
async def image_to_pdf(output_name: str = "jarvis_output.pdf"):
    """
    COMPLETE JARVIS FEATURE: Select image → Convert to PDF → TTS feedback.
    Trigger: python this_script.py OR await in Jarvis voice loop.
    """
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)  # Stays on top like your HUD
    
    speak("Select an image to convert to PDF.")  # Voice prompt
    
    # Native File Explorer dialog - SINGLE image only
    image_path = filedialog.askopenfilename(
        title="🧠 JARVIS: Select ONE Image for PDF",
        filetypes=[
            ("All Images", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.webp"),
            ("JPEG", "*.jpg *.jpeg"),
            ("PNG", "*.png")
        ]
    )
    
    if not image_path:
        speak("Conversion cancelled.")
        root.destroy()
        return "No image selected."
    
    try:
        speak("Converting your image to PDF...")
        
        # Load & prepare image (auto RGB for PDF)
        img = Image.open(image_path)
        filename = Path(image_path).stem
        pdf_path = Path(f"{filename}_by_jarvis.pdf")
        
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # High-quality PDF save (single page)
        img.save(pdf_path, "PDF", resolution=150.0, quality=95)
        
        result = f"Jarvis created: {pdf_path.absolute()}"
        speak(result)
        
        # Success popup (your style)
        messagebox.showinfo("✅ JARVIS SUCCESS", 
                           f"PDF saved!\n{pdf_path.absolute()}")
        
        root.destroy()
        return result
        
    except Exception as e:
        error = f"Error: {str(e)}"
        speak(error)
        messagebox.showerror("❌ JARVIS ERROR", error)
        root.destroy()
        return error

# DIRECT RUN or ASYNC INTEGRATION
if __name__ == "__main__":
    print("🧠 JARVIS Image-to-PDF Ready! (Ctrl+C to exit)")
    asyncio.run(image_to_pdf())
