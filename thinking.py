import psutil
import time
import threading
import schedule
import requests
from datetime import datetime, timedelta
import speech_recognition as sr
import pyttsx3
import google.auth
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os
import subprocess
from collections import defaultdict

class JarvisAutoThinking:
    def __init__(self):
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty('rate', 180)
        self.tts_engine.setProperty('volume', 0.9)
        
        # Activity tracking
        self.activity_history = defaultdict(list)
        self.last_break_time = datetime.now()
        self.CODING_THRESHOLD = 3 * 60 * 60  # 3 hours
        self.WORK_THRESHOLD = 1 * 60 * 60    # 1 hour
        
        # Reminders
        self.reminders = {
            "GitHub 2FA": "2026-03-15",  # Deadline example
            "Project Demo": "2026-03-10"
        }
        
        # Start monitoring
        self.monitoring_thread = threading.Thread(target=self.activity_monitor, daemon=True)
        self.monitoring_thread.start()
        self.schedule_reminders()
        
    def speak(self, text):
        """Natural speech with Jarvis-like personality"""
        responses = {
            "break": ["Sir, aap 3 ghante se code kar rahe ho, break le lo. Coffee piyenge?", 
                     "Boss, eyes ko rest do, 3 hours non-stop coding ho gaya!"],
            "meeting": ["Sir, meeting 10 min mein hai. Prep kar lo.",
                       "10 minutes mein meeting hai, screen share ready hai?"],
            "deadline": ["GitHub 2FA deadline 2 din mein hai, abhi setup kar do.",
                        "Reminder: GitHub security update pending hai!"]
        }
        
        import random
        if any(kw in text.lower() for kw in responses):
            text = random.choice(responses[next(kw for kw in responses if kw in text.lower())])
        
        print(f"🧠 JARVIS: {text}")
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()
    
    def get_current_activity(self):
        """Detect current activity (coding/debugging)"""
        process = psutil.Process(os.getpid())
        cmdline = ' '.join(process.cmdline()).lower()
        
        coding_keywords = ['python', 'vscode', 'code', 'pycharm', 'debug', 'git']
        if any(keyword in cmdline for keyword in coding_keywords):
            return "coding"
        
        # Check foreground window (Windows)
        try:
            result = subprocess.run(['powershell', '-Command', 
                '(Get-Process | Where-Object {$_.MainWindowTitle -ne ""}).MainWindowTitle | Select-Object -First 1'],
                capture_output=True, text=True, timeout=2)
            window = result.stdout.strip().lower()
            if any(kw in window for kw in ['visual studio', 'code', 'terminal', 'cmd', 'powershell']):
                return "coding"
        except:
            pass
            
        return "other"
    
    def activity_monitor(self):
        """Monitor coding activity and suggest breaks"""
        while True:
            current_activity = self.get_current_activity()
            now = datetime.now()
            
            if current_activity == "coding":
                self.activity_history["coding"].append(now)
                
                # Check for 3-hour coding session
                recent_activity = [t for t in self.activity_history["coding"] 
                                 if now - t < timedelta(hours=3)]
                if len(recent_activity) > 10 and (now - self.last_break_time) > timedelta(hours=3):
                    self.speak("break")
                    self.last_break_time = now
            
            time.sleep(300)  # Check every 5 minutes
    
    def check_calendar(self):
        """Google Calendar integration"""
        try:
            # Setup Google Calendar API (requires credentials.json)
            creds = Credentials.from_authorized_user_file('token.json', 
                                                        ['https://www.googleapis.com/auth/calendar.readonly'])
            service = build('calendar', 'v3', credentials=creds)
            
            now = datetime.utcnow().isoformat() + 'Z'
            events_result = service.events().list(calendarId='primary', timeMin=now,
                                                maxResults=10, singleEvents=True,
                                                orderBy='startTime').execute()
            events = events_result.get('items', [])
            
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                
                if start_dt - datetime.now() < timedelta(minutes=10):
                    title = event['summary']
                    self.speak(f"meeting - {title}")
                    
        except Exception as e:
            print(f"Calendar check failed: {e}")
    
    def check_reminders(self):
        """Check deadlines and reminders"""
        now = datetime.now()
        for task, deadline_str in self.reminders.items():
            deadline = datetime.strptime(deadline_str, "%Y-%m-%d")
            days_left = (deadline - now).days
            
            if 0 < days_left <= 2:
                self.speak(f"deadline - {task}")
    
    def schedule_reminders(self):
        """Schedule regular checks"""
        schedule.every(10).minutes.do(self.check_calendar)
        schedule.every(30).minutes.do(self.check_reminders)
        
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
    
    def add_reminder(self, task, date_str):
        """Add custom reminder"""
        self.reminders[task] = date_str
        self.speak(f"Reminder added: {task} on {date_str}")

# Usage Example
if __name__ == "__main__":
    jarvis = JarvisAutoThinking()
    
    # Test reminders
    jarvis.add_reminder("Project Review", "2026-03-07")
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Jarvis Auto-Thinking stopped.")
