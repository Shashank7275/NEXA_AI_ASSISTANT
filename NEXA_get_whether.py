import os
import requests
import logging
from dotenv import load_dotenv
from livekit.agents import function_tool  # ✅ Correct decorator

load_dotenv()
if not os.getenv("OPENWEATHER_API_KEY"):
    base_dir = os.path.dirname(__file__)
    try:
        import sys as _sys
        if getattr(_sys, "frozen", False):
            base_dir = os.path.dirname(_sys.executable)
    except Exception:
        pass
    for _p in [os.path.join(base_dir, ".env"), os.path.join(os.path.dirname(base_dir), ".env")]:
        try:
            if os.path.exists(_p):
                load_dotenv(_p)
                break
        except Exception:
            pass


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def detect_city_by_ip() -> str:
    try:
        logger.info("IP के ज़रिए शहर detect करने की कोशिश की जा रही है")
        ip_info = requests.get("https://ipapi.co/json/").json()
        city = ip_info.get("city")
        if city:
            logger.info(f"IP से शहर Detect किया गया: {city}")
            return city
        else:
            logger.warning("City detect करने में विफल, default 'Delhi' इस्तेमाल किया जा रहा है।")
            return "Delhi"
    except Exception as e:
        logger.error(f"IP से city detect करने में error आया: {e}")
        return "Delhi"

@function_tool
async def get_weather(city: str = "") -> str:
    
    api_key = os.getenv("OPENWEATHER_API_KEY")

    if not api_key:
        logger.error("OpenWeather API key missing है।")
        return "Environment variables में OpenWeather API key नहीं मिली।"

    if not city:
        city = detect_city_by_ip()

    logger.info(f"City के लिए weather fetch किया जा रहा है।: {city}")
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric"
    }

    try:
        response = requests.get(url, params=params)
        if response.status_code != 200:
            logger.error(f"OpenWeather API में error आया।: {response.status_code} - {response.text}")
            return f"Error: {city} के लिए weather fetch नहीं कर पाए। कृपया city name चेक करें।"

        data = response.json()
        weather = data["weather"][0]["description"].title()
        temperature = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]

        result = (f"Weather in {city}:\n"
                  f"- Condition: {weather}\n"
                  f"- Temperature: {temperature}°C\n"
                  f"- Humidity: {humidity}%\n"
                  f"- Wind Speed: {wind_speed} m/s")

        logger.info(f"Weather result: \n{result}")
        return result

    except Exception as e:
        logger.exception(f"Weather fetch करते समय exception आया: {e}")
        return "Weather fetch करते समय एक error आया"
    
if __name__ == "__main__":
    import threading
    import tkinter as tk
    from tkinter import ttk
    import sys

    root = tk.Tk()
    root.title("Jarvis Launcher")
    root.geometry("420x220")

    notebook = ttk.Notebook(root)
    tab = ttk.Frame(notebook)
    notebook.add(tab, text="Agent")
    notebook.pack(fill="both", expand=True, padx=10, pady=10)

    status_var = tk.StringVar(value="Idle")
    status_label = ttk.Label(tab, textvariable=status_var)
    status_label.pack(pady=(10, 6))

    agent_thread = {"t": None}

    def start_agent():
        if agent_thread["t"] and agent_thread["t"].is_alive():
            status_var.set("Already running")
            return

        def runner():
            try:
                status_var.set("Starting...")
                from livekit import agents as lk_agents
                import agent as agent_mod
                lk_agents.cli.run_app(lk_agents.WorkerOptions(entrypoint_fnc=agent_mod.entrypoint))
            except Exception as e:
                status_var.set(f"Error: {e}")

        t = threading.Thread(target=runner, daemon=True)
        agent_thread["t"] = t
        t.start()
        status_var.set("Running")

    start_btn = ttk.Button(tab, text="Start Agent", command=start_agent)
    start_btn.pack(pady=10)

    root.mainloop()
