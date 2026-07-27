# 🤖 Jarvis Advanced Setup Guide (LiveKit + Google Realtime API)

This guide explains EVERYTHING step‑by‑step in simple Hinglish + English. Follow line by line.

---

# 📌 Overview (What is happening internally)

When you run:

```
python agent.py console
```

Jarvis performs these steps:

1. Load environment variables (.env)
2. Connect to LiveKit Cloud
3. Initialize Google Realtime API
4. Setup microphone input
5. Send instructions to Google
6. Receive response
7. Speak reply
8. Save memory

Your error happens in Step 5.

---

# STEP 1: Verify Folder Structure

Your project should look like this:

```
Jarvis/
│
├── agent.py
├── memory.py
├── test_memory_persistence.py
├── jarvis_gui.py
├── .env
├── requirements.txt
└── .venv/
```

Explanation:

agent.py → Main brain
memory.py → Memory system
.env → API keys
.venv → Python virtual environment

---

# STEP 2: Activate Virtual Environment

Open terminal in project folder:

```
cd path/to/Jarvis
```

Activate:

Windows:

```
.venv\Scripts\activate
```

Expected output:

```
(.venv) C:\Users\...
```

Means environment is active.

---

# STEP 3: Verify API Key

Open .env file

It should contain:

```
GOOGLE_API_KEY=your_api_key_here
LIVEKIT_URL=wss://jarvis-xxxx.livekit.cloud
LIVEKIT_API_KEY=xxxx
LIVEKIT_API_SECRET=xxxx
```

Test key:

```
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('GOOGLE_API_KEY'))"
```

Expected output:

```
AIzaSyXXXX
```

If None → .env not loading

---

# STEP 4: Verify Internet Connection

Run:

```
ping generativelanguage.googleapis.com
```

Expected:

```
Reply from...
```

If Request timed out → network issue

Fix:

Disable VPN
Restart router

---

# STEP 5: Test Google API Directly

https://aistudio.google.com/?project=gen-lang-client-0994700916

Create test_google.py

```
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")

response = model.generate_content("Hello")

print(response.text)
```

Run:

```
python test_google.py
```

Expected:

```
Hello! How can I help you?
```

If error → API issue

---

# STEP 6: Verify LiveKit Connection

https://docs.livekit.io/agents/start/voice-ai-quickstart/

Run:

```
python -c "from livekit.agents import config; print(config.settings.livekit_url)"
```

Expected:

```
wss://jarvis-xxxx.livekit.cloud
```

If None → LiveKit not configured

---

# STEP 7: Disable Memory Temporarily (IMPORTANT)

Open agent.py

Find:

```
ENABLE_MEMORY_INTERCEPTOR = True
```

Change:

```
ENABLE_MEMORY_INTERCEPTOR = False
```

Why:

Removes extra async load

---

# STEP 8: Run Jarvis

Run:

```
python agent.py console
```

Expected:

```
Connected to LiveKit
Google setupComplete received
Jarvis ready
```

---

# STEP 9: Verify Microphone

Windows:

Settings
Sound
Input

Test microphone

If mic not working → timeout occurs

---

# STEP 10: Increase Timeout (Advanced Fix)

Open agent.py

Find realtime config:

Change timeout:

```
timeout=60
```

Instead of:

```
timeout=30
```

---

# STEP 11: Verify Python Version

Run:

```
python --version
```

Required:

```
Python 3.10 or 3.11
```

Not supported:

3.13

---

# STEP 12: Reinstall Dependencies

Run:

```
pip install -r requirements.txt --force-reinstall
```

---

# STEP 13: Final Test Flow

Start:

```
python agent.py console
```

Then speak:

```
Hello Jarvis
```

Expected:

```
Jarvis replies
```

---

# Root Cause of Your Error

Error:

```
generate_reply timed out
```

Means:

Jarvis connected
BUT
Google did not respond

Causes:

• Internet slow
• API key invalid
• Timeout too low
• Microphone not ready
• VPN blocking

---

# BEST WORKING CONFIG (Recommended)

Python: 3.11
LiveKit: latest
Gemini realtime: enabled
Memory: enabled after test
Timeout: 60 seconds

---

# FINAL SUCCESS OUTPUT

You should see:

```
LiveKit Connected
Google setupComplete received
Listening...
User speaking...
Jarvis responding...
```

---

# If Still Not Working

Solution:

Use gemini‑1.5‑flash instead realtime

Realtime is unstable sometimes

---

# DONE

Your Jarvis will work perfectly after this setup.

---

If you want, I can also give fully optimized agent.py file.
