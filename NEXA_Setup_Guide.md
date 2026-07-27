# 🤖 NEXA AI Assistant – Complete Setup Guide

> **NEXA AI Assistant** is an advanced AI desktop assistant built using Python, Google Gemini, LiveKit, automation tools, web search, weather APIs, memory, and voice interaction.

---

# 📋 System Requirements

Before starting, make sure you have:

* Windows 10/11 (64-bit)
* Python 3.11+ (Recommended)
* Git
* VS Code (Recommended)
* Internet Connection

Check Python version:

```bash
python --version
```

or

```bash
py --version
```

Expected Output

```
Python 3.11.x
```

---

# 📂 Clone the Project

```bash
git clone <your_repository_url>

cd NEXA_AI_ASSISTANT
```

or simply open the project folder.

---

# 🟢 STEP 1 — Create Virtual Environment (.venv)

Inside the project folder run:

```bash
python -m venv .venv
```

If Python command doesn't work

```bash
py -m venv .venv
```

After creating the environment activate it.

## Windows CMD

```cmd
.venv\Scripts\activate
```

## Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate again

```powershell
.venv\Scripts\Activate.ps1
```

## Git Bash

```bash
source .venv/Scripts/activate
```

When activated you'll see

```
(.venv)
```

before your terminal path.

---

# 🟢 STEP 2 — Upgrade pip

Always upgrade pip before installing packages.

```bash
python -m pip install --upgrade pip
```

Verify version

```bash
pip --version
```

---

# 🟢 STEP 3 — Install Requirements

```bash
pip install -r requirements.txt
```

Wait until every package finishes installing.

---

# 🟢 STEP 4 — Create Environment Variables

Create a file named

```
.env
```

inside the project root.

Paste the following:

```env
# -----------------------------
# LiveKit
# -----------------------------

LIVEKIT_URL=
LIVEKIT_API_KEY=
LIVEKIT_API_SECRET=

# -----------------------------
# Google Gemini
# -----------------------------

GOOGLE_API_KEY=

# -----------------------------
# Google Custom Search
# -----------------------------

GOOGLE_SEARCH_API_KEY=
SEARCH_ENGINE_ID=

# -----------------------------
# OpenWeather
# -----------------------------

OPENWEATHER_API_KEY=

# -----------------------------
# OpenAI
# -----------------------------

OPENAI_API_KEY=
```

Fill every API key before running the project.

---

# 🟢 STEP 5 — Create Memory Folder

Inside the project create a folder named

```
memory
```

Project structure

```
NEXA_AI_ASSISTANT/

│
├── agent.py
├── requirements.txt
├── .env
├── README.md
│
├── memory/
│      └── Nexa_memory.py
│
├── Nexa_gui.py
├── 

...
```

Move

```
Nexa_memory.py
```

inside the

```
memory
```

folder.

---

# 🟢 STEP 6 — Verify Project Structure

```
NEXA_AI_ASSISTANT

│
├── .venv
├── .env
├── README.md
├── requirements.txt
├── agent.py
│
├── memory
│      └── Nexa_memory.py
│
├── Nexa_gui.py
├── Nexa_prompt.py
├── 
└── ...
```

---

# 🟢 STEP 7 — Run NEXA

Activate virtual environment

```
.venv\Scripts\activate
```

Run

```bash
python agent.py console
```

If everything is configured correctly you'll see NEXA starting inside the terminal.

---

# 🎉 Congratulations

NEXA AI Assistant is now running.

---

# ⚠ Common Errors & Solutions

---

## ❌ python is not recognized

Error

```
'python' is not recognized...
```

Solution

Install Python from the official installer and ensure **Add Python to PATH** is checked during installation.

Verify

```bash
python --version
```

---

## ❌ No module named ...

Example

```
ModuleNotFoundError
```

Solution

```bash
pip install -r requirements.txt
```

or

```bash
pip install package_name
```

---

## ❌ Virtual Environment not activated

If terminal doesn't show

```
(.venv)
```

activate it

```bash
.venv\Scripts\activate
```

---

## ❌ pip command not found

Use

```bash
python -m pip install -r requirements.txt
```

---

## ❌ Permission Denied

Run Terminal

**As Administrator**

or

```powershell
Set-ExecutionPolicy RemoteSigned
```

---

## ❌ Missing .env file

Error

```
Environment Variable Not Found
```

Solution

Create

```
.env
```

Add all required API keys.

---

## ❌ Google Gemini Error

```
GOOGLE_API_KEY not found
```

Solution

Add

```env
GOOGLE_API_KEY=YOUR_KEY
```

inside

```
.env
```

---

## ❌ LiveKit Connection Failed

Verify

```
LIVEKIT_URL
LIVEKIT_API_KEY
LIVEKIT_API_SECRET
```

All three values must be valid.

---

## ❌ Google Search Doesn't Work

Verify

```
GOOGLE_SEARCH_API_KEY
SEARCH_ENGINE_ID
```

Both values are required.

---

## ❌ Weather API Error

Add

```env
OPENWEATHER_API_KEY=
```

inside

```
.env
```

---

## ❌ OpenAI Error

Add

```env
OPENAI_API_KEY=
```

---

## ❌ Memory Not Working

Create

```
memory/
```

folder.

Move

```
Nexa_memory.py
```

inside

```
memory/
```

Verify the import path matches the folder structure.

---

## ❌ FileNotFoundError

Ensure all files exist:

```
agent.py

requirements.txt

.env

memory/

Nexa_memory.py
```

---

## ❌ ImportError

Run

```bash
pip install -r requirements.txt
```

or reinstall the missing package.

---



---

## ❌ API Key Invalid

Double-check:

* Correct API key
* No extra spaces
* No quotation marks unless required
* API enabled in the provider dashboard
* Billing/quota (if applicable)

---

## ❌ Agent Doesn't Start

Run

```bash
python agent.py console
```

instead of

```bash
python agent.py
```

---

## 🔄 Reinstall Everything (Fresh Setup)

Delete

```
.venv
```

Create again

```bash
python -m venv .venv
```

Activate

```bash
.venv\Scripts\activate
```

Upgrade pip

```bash
python -m pip install --upgrade pip
```

Install requirements

```bash
pip install -r requirements.txt
```

Run

```bash
python agent.py console
```

---

# 🚀 Features

* 🎙️ Voice Assistant
* 🤖 Google Gemini AI
* 🌐 Google Search Integration
* 🌦️ Real-Time Weather
* 🧠 Persistent Memory System
* 💬 Conversational AI
* 🖥️ Desktop Automation
* ⚡ Fast Responses
* 🔊 Speech Recognition
* 🔈 Text-to-Speech
* 📂 File & Application Control
* 🧩 Modular Architecture
* 🔐 Secure API Configuration via `.env`

---

# 💡 Tips

* Always activate `.venv` before running the assistant.
* Never commit your `.env` file to GitHub.
* Keep `requirements.txt` updated after installing new packages.
* Store all secrets only in `.env`.
* Back up your `memory/` folder if you want to preserve conversations.

---

# ❤️ Built With

* Python
* Google Gemini
* LiveKit
* OpenAI
* OpenWeather API
* Google Custom Search API
* dotenv
* AsyncIO
* Modern AI Agent Architecture

---

# ▶️ Quick Start

```bash
git clone <repository>

cd NEXA_AI_ASSISTANT

python -m venv .venv

.venv\Scripts\activate

python -m pip install --upgrade pip

pip install -r requirements.txt

# Create .env and add all API keys

python agent.py console
```

---

# 📜 License

This project is intended for educational and personal use unless otherwise specified by the repository license.
