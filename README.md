# 🤖 NEXA AI Assistant

> **NEXA AI Assistant** is a Python-based desktop AI assistant powered by Google Gemini and LiveKit. It combines voice interaction,
> persistent memory, web search, weather information, desktop automation, file control, image generation, object detection, and other
> useful tools in one modular AI agent.


---

## ✨ Features

- 🎙️ Voice-based AI assistant
- 🤖 Google Gemini real-time AI
- 🧠 Persistent conversation memory
- 🌐 Google/web search integration
- 🌦️ Real-time weather information
- 🖥️ Windows desktop automation
- 🖱️ Keyboard and mouse control
- 📂 File and application control
- 📸 Screenshot functionality
- 🎨 AI image generation
- 👁️ Object detection with YOLO
- 📄 Image-to-PDF conversion
- ▶️ YouTube controls
- 🛒 Flipkart automation tools
- 🌍 IP information
- 🔊 Text-to-speech support
- 🧩 Modular tool-based agent architecture
- 🔐 API keys loaded through environment variables

The main agent registers these tools and starts the LiveKit agent session from `agent.py`. citeturn1view0

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core language |
| Google Gemini | AI / real-time model |
| LiveKit Agents | Real-time AI agent runtime |
| LiveKit Plugins | Google, OpenAI, Silero, noise cancellation |
| LangChain Community | AI integrations |
| PyAutoGUI / Pynput | Keyboard and mouse automation |
| OpenCV / MediaPipe | Computer vision |
| Ultralytics YOLO | Object detection |
| Selenium | Browser automation |
| BeautifulSoup | Web parsing |
| Pillow | Image processing |
| python-dotenv | Environment configuration |

The repository's current `requirements.txt` includes these major dependencies and related packages. citeturn2view0

---

# 🚀 Installation

## 1. Prerequisites

Recommended environment:

- Windows 10/11
- Python **3.11**
- Git
- VS Code
- Internet connection
- Working microphone/audio input
- API accounts/keys for the services you want to use

The project's setup guide recommends Python 3.11+. citeturn3view0

Check your Python version:

```bash
python --version
```

Expected:

```text
Python 3.11.x
```

> Python 3.10 may work for some dependencies, but **Python 3.11 is the recommended version for this project**.

---

## 2. Clone the Repository

```bash
git clone https://github.com/Shashank7275/NEXA_AI_ASSISTANT.git
cd NEXA_AI_ASSISTANT
```

---

## 3. Create a Virtual Environment

Create `.venv`:

```bash
python -m venv .venv
```

### Windows CMD

```bash
.venv\Scripts\activate
```

### Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then:

```powershell
.venv\Scripts\Activate.ps1
```

After activation, your terminal should show:

```text
(.venv)
```

---

## 4. Upgrade pip

```bash
python -m pip install --upgrade pip
```

---

## 5. Install Dependencies

Make sure the file is named exactly:

```text
requirements.txt
```

Then run:

```bash
pip install -r requirements.txt
```

The repository currently contains a `requirements.txt` with LiveKit, Google/OpenAI plugins, LangChain Community, requests, dotenv, browser automation, computer-vision and other dependencies. citeturn2view0

---

# 🔐 API Configuration

Create a file named:

```text
.env
```

in the project root.

Example:

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

The current project setup guide lists these environment variables, and `agent.py` explicitly loads `GOOGLE_API_KEY` from the environment. citeturn3view0turn1view0

### ⚠️ Security

**Never publish real API keys on GitHub.**

Your `.env` should be ignored by Git:

```gitignore
.env
.venv/
__pycache__/
*.pyc
```

If a real API key has ever been committed to a public GitHub repository, **revoke/rotate that key immediately** and replace it with a new one.

---

# 🧠 Memory Setup

The current `agent.py` imports memory modules using:

```python
from memory.jarvis_memory import (
    load_memory,
    save_memory,
    get_recent_conversations,
    add_memory_entry
)
```

Therefore, make sure your project contains the expected package/module structure:

```text
NEXA_AI_ASSISTANT/
│
├── memory/
│   ├── __init__.py
│   └── jarvis_memory.py
│
├── agent.py
├── NEXA_gui.py
├── requirements.txt
├── .env
└── ...
```

> If your memory file is currently named `Nexa_memory.py` in the root folder, rename/move it to match the import used by `agent.py`, or update the import in `agent.py`.

---

# 📁 Project Structure

Important files/modules in the repository include:

```text
NEXA_AI_ASSISTANT/
│
├── .env
├── requirements.txt
├── agent.py
├── NEXA_gui.py
├── NEXA_prompts.py
├── NEXA_google_search.py
├── NEXA_get_whether.py
├── NEXA_screenshot.py
├── NEXA_file_open.py
├── NEXA_window_CTRL.py
├── keyboard_mouse_CTRL.py
├── automation.py
├── thinking.py
├── memory_interceptor.py
├── file_search.py
├── image_generate.py
├── image_to_pdf.py
├── object_detection.py
├── ip_address.py
├── youtube.py
├── flipkart.py
├── diagnose_api.py
├── main.py
│
├── memory/
│   └── jarvis_memory.py
│
└── tests/
    ├── test_google_api.py
    ├── test_memory_direct.py
    └── test_memory_retrieve.py
```

The repository currently contains the corresponding agent, automation, search, memory, vision, image, YouTube, shopping and test modules. citeturn0view0

---

# ▶️ Run NEXA

After activating `.venv` and configuring `.env`:

```bash
python agent.py console
```

This is the recommended console launch command documented for the project. citeturn3view0

The `agent.py` entry point also starts `NEXA_gui.py` as a separate process when the GUI file is available. citeturn1view0

---

# 🧪 Testing

Run individual tests, for example:

```bash
python test_google_api.py
python test_memory_direct.py
python test_memory_retrieve.py
```

You can also add more automated tests as the project grows.

---

# 🛠️ Troubleshooting

### `python is not recognized`

Install Python 3.11 and enable:

```text
Add Python to PATH
```

Then restart VS Code/Terminal.

Check:

```bash
python --version
```

### `ModuleNotFoundError`

Make sure `.venv` is activated:

```bash
.venv\Scripts\activate
```

Then:

```bash
pip install -r requirements.txt
```

### `GOOGLE_API_KEY not found`

Check that `.env` exists in the project root:

```env
GOOGLE_API_KEY=YOUR_KEY
```

### LiveKit connection error

Verify:

```env
LIVEKIT_URL=YOUR_URL
LIVEKIT_API_KEY=YOUR_KEY
LIVEKIT_API_SECRET=YOUR_SECRET
```

### Google Search not working

Verify:

```env
GOOGLE_SEARCH_API_KEY=YOUR_KEY
SEARCH_ENGINE_ID=YOUR_ID
```

### Weather not working

Verify:

```env
OPENWEATHER_API_KEY=YOUR_KEY
```

### Memory not working

Verify that the memory package/module matches the import used by `agent.py`:

```text
memory/jarvis_memory.py
```

---

# 🔒 Important Safety & Privacy Notes

NEXA includes powerful desktop automation capabilities such as keyboard/mouse control, file operations, browser automation and purchasing-related tools.

Use these tools carefully and only on systems/accounts where you have permission.

Never hard-code:

- API keys
- passwords
- access tokens
- LiveKit secrets
- private credentials

Keep secrets inside `.env` and keep `.env` out of Git.

---

# 📌 Roadmap

- [ ] Improve GUI/UX
- [ ] Add stronger automated test coverage
- [ ] Add `.env.example`
- [ ] Add CI/CD with GitHub Actions
- [ ] Improve documentation
- [ ] Add installation script
- [ ] Improve error handling and logging
- [ ] Add more AI tools
- [ ] Add production deployment documentation

---

# 🤝 Contributing

Contributions, bug reports and feature ideas are welcome.

### 1. Fork the repository

### 2. Create a branch

```bash
git checkout -b feature/your-feature
```

### 3. Make your changes

### 4. Test your changes

```bash
python test_google_api.py
python test_memory_direct.py
python test_memory_retrieve.py
```

### 5. Commit

```bash
git add .
git commit -m "Add: your feature"
```

### 6. Push

```bash
git push origin feature/your-feature
```

### 7. Open a Pull Request

Please describe what you changed and how you tested it.

---

# 📜 License

This project is licensed under the **MIT License**.

See the [`LICENSE`](LICENSE) file for the complete license text.

> If your repository uses a different license, change this section to match the actual `LICENSE` file.

---

# 👨‍💻 Author

**Shashank Singh**

GitHub: [@Shashank7275](https://github.com/Shashank7275)

Project: [NEXA AI ASSISTANT](https://github.com/Shashank7275/NEXA_AI_ASSISTANT)

---

## ⭐ Support the Project

If NEXA AI Assistant is useful to you:

- ⭐ Star the repository
- 🍴 Fork it
- 🐛 Report bugs
- 💡 Suggest features
- 🤝 Contribute improvements

**Built with Python, AI, automation and a lot of experimentation. 🚀**
