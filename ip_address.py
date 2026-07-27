import requests
import pyttsx3
import os
import json
from livekit.agents import function_tool



# Initialize Text-to-Speech Engine
engine = pyttsx3.init()
engine.setProperty('rate', 170)

def speak(text):
    engine.say(text)
    engine.runAndWait()

def get_ip_address():
    """
    Get Public IP Address
    """
    try:
        ip_response = requests.get("https://api.ipify.org?format=json", timeout=5)
        ip_data = ip_response.json()
        return ip_data["ip"]
    except:
        return None

def get_ip_location():
    try:
        ip = get_ip_address()
        
        if not ip:
            speak("Unable to fetch your IP address.")
            return
        
        response = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
        data = response.json()

        if data["status"] != "success":
            speak("Location service failed.")
            return
        
        if data.get("city") == "Ghaziabad":
            data["city"] = "Noida"
        
        try:
            out_path = os.path.join(os.path.dirname(__file__), "ip.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

        city = data.get("city", "Unknown city")
        region = data.get("regionName", "Unknown state")
        country = data.get("country", "Unknown country")
        isp = data.get("isp", "Unknown provider")
        lat = data.get("lat")
        lon = data.get("lon")

        result = f"""
        Your IP address is {ip}.
        You are located in {city}, {region}, {country}.
        Your Internet Service Provider is {isp}.
        """

        print("------ IP DETAILS ------")
        print("IP Address :", ip)
        print("City       :", city)
        print("State      :", region)
        print("Country    :", country)
        print("ISP        :", isp)
        print("Latitude   :", lat)
        print("Longitude  :", lon)
        print("------------------------")

        speak(f"You are in {city}, {region}, {country}")

    except Exception as e:
        print("Error:", e)
        speak("Sorry, I am unable to fetch your location.")

# Run function directly
if __name__ == "__main__":
    get_ip_location()

@function_tool(name="get_ip_info", description="Public IP और लोकेशन निकालकर ip.json update करे और Hindi में जवाब दे")
async def get_ip_info() -> str:
    try:
        ip = get_ip_address()
        if not ip:
            return "क्षमा करें, अभी आपका आईपी पता उपलब्ध नहीं है।"
        response = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
        data = response.json()
        if data.get("status") != "success":
            return "लोकेशन सेवा उपलब्ध नहीं है।"
        if data.get("city") == "Ghaziabad":
            data["city"] = "Noida"
        try:
            out_path = os.path.join(os.path.dirname(__file__), "ip.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception:
            pass
        city = data.get("city") or "अज्ञात शहर"
        region = data.get("regionName") or "अज्ञात राज्य"
        country = data.get("country") or "अज्ञात देश"
        isp = data.get("isp") or "अज्ञात प्रदाता"
        lat = data.get("lat")
        lon = data.get("lon")
        ip_text = data.get("query", ip or "")
        # Concise Hindi response for Jarvis voice
        if lat is not None and lon is not None:
            return f"आपका आई पी {ip_text} है। आप {city}, {region}, {country} में हैं। लोकेशन कोऑर्डिनेट्स {lat}, {lon} और प्रदाता {isp}।"
        else:
            return f"आपका आई पी {ip_text} है। आप {city}, {region}, {country} में हैं। प्रदाता {isp}।"
    except Exception as e:
        return f"त्रुटि: {e}"


