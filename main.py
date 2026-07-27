import tkinter as tk
from tkinter import ttk
import threading
import sys
from pathlib import Path
import voice
from flipkart import FlipkartScraper
import automation as auto

class JarvisGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("JARVIS - AI Assistant")
        self.root.geometry("1200x800")
        self.root.configure(bg='black')
        
        self.voice_engine = voice.VoiceEngine()
        self.flipkart = FlipkartScraper()
        self.auto_core = auto.AutomationCore()
        
        self.setup_ui()
        self.start_listening()
    
    def setup_ui(self):
        # Main frame with sci-fi styling
        main_frame = tk.Frame(self.root, bg='black')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title = tk.Label(main_frame, text="JARVIS", font=("Arial", 48, "bold"), 
                        fg="#00FFFF", bg='black')
        title.pack(pady=(0, 20))
        
        # Command input
        input_frame = tk.Frame(main_frame, bg='black')
        input_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.command_var = tk.StringVar()
        self.command_entry = tk.Entry(input_frame, textvariable=self.command_var,
                                    font=("Arial", 16), bg="#1a1a1a", fg="white",
                                    insertbackground="white")
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.command_entry.bind('<Return>', self.execute_command)
        
        tk.Button(input_frame, text="EXECUTE", command=self.execute_command,
                 bg="#FF4444", fg="white", font=("Arial", 12, "bold")).pack()
        
        # Status and logs
        self.log_text = tk.Text(main_frame, height=20, bg="#0a0a0a", fg="#00FF00",
                              font=("Courier", 12), insertbackground="white")
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def log(self, message):
        self.log_text.insert(tk.END, f"[{voice.get_time()}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def start_listening(self):
        threading.Thread(target=self.voice_engine.listen_continuously, 
                        args=(self.execute_command_voice,), daemon=True).start()
    
    def execute_command(self, event=None):
        cmd = self.command_var.get().lower().strip()
        self.command_var.set("")
        self.log(f"Command: {cmd}")
        
        if "flipkart" in cmd:
            threading.Thread(target=self.handle_flipkart, args=(cmd,)).start()
        elif "automation" in cmd or cmd in ["status", "system", "monitor"]:
            threading.Thread(target=self.handle_automation, args=(cmd,)).start()
        else:
            self.voice_engine.speak("Command executed")
    
    def execute_command_voice(self, command):
        self.root.after(0, lambda: self.execute_command_from_voice(command))
    
    def execute_command_from_voice(self, command):
        self.log(f"Voice: {command}")
        self.command_var.set(command)
        self.execute_command()
    
    def handle_flipkart(self, cmd):
        if "search" in cmd:
            query = cmd.replace("flipkart search", "").strip()
            results = self.flipkart.search_products(query)
            self.root.after(0, lambda: self.log(f"Flipkart: {len(results)} results found"))
        elif "buy" in cmd or "order" in cmd:
            query = cmd.replace("flipkart", "").replace("buy", "").replace("order", "").strip()
            if "online" in cmd:
                result = self.flipkart.buy_auto(query, payment="online")
                self.root.after(0, lambda: self.log(f"Flipkart: {result}"))
            elif "auto" in cmd or "cod" in cmd:
                result = self.flipkart.buy_cod_auto(query)
                self.root.after(0, lambda: self.log(f"Flipkart: {result}"))
            else:
                url = self.flipkart.open_product(query)
                self.root.after(0, lambda: self.log(f"Flipkart: opened {url if url else 'no product found'}"))
    
    def handle_automation(self, cmd):
        status = self.auto_core.get_system_status()
        self.root.after(0, lambda: self.log(f"System: CPU {status['cpu']}% | RAM {status['ram']}GB"))

if __name__ == "__main__":
    root = tk.Tk()
    app = JarvisGUI(root)
    root.mainloop()
