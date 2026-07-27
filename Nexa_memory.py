import speech_recognition as sr
import pyttsx3
import json
import os
from datetime import datetime
from livekit.agents import function_tool

# --- कॉन्फ़िगरेशन ---
MEMORY_FILE = os.path.join(os.path.dirname(__file__), "memory.json")

# ==============================================================================
# 1. कोर इंजन कंपोनेंट्स (Core Engine Components)
# ==============================================================================

try:
    engine = pyttsx3.init('sapi5')
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[0].id)
except Exception as e:
    print(f"TTS Engine Error: {e}")
    engine = None

def speak(audio):
    """इस फंक्शन से Jarvis बोलता है और बातचीत को मेमोरी में सेव करता है"""
    print(f"Jarvis: {audio}")
    if engine:
        engine.say(audio)
        engine.runAndWait()
    append_conversation_sync("jarvis", audio)

def take_command():
    """माइक्रोफोन से सुनता है, टेक्स्ट में बदलता है और बातचीत को सेव करता है"""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.pause_threshold = 1
        r.adjust_for_ambient_noise(source)
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=5)
        except sr.WaitTimeoutError:
            print("Listening timed out.")
            return "None"

    try:
        print("Recognizing...")
        query = r.recognize_google(audio, language='hi-IN')
        print(f"User said: {query}\n")
        append_conversation_sync("user", query)
        return query.lower()
    except Exception:
        print("Sorry, I did not understand that.")
        return "None"

# ==============================================================================
# 2. मेमोरी मैनेजमेंट फंक्शन्स (Memory Management Functions)
# ==============================================================================

def load_memory_sync():
    """JSON फाइल से मेमोरी लोड करता है"""
    if not os.path.exists(MEMORY_FILE):
        return {"facts": {}, "conversation": []}
    
    with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            if "facts" not in data: data["facts"] = {}
            if "conversation" not in data: data["conversation"] = []
            return data
        except json.JSONDecodeError:
            return {"facts": {}, "conversation": []}

def save_memory_sync(data: dict):
    """मेमोरी को JSON फाइल में सेव करता है"""
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def append_conversation_sync(speaker: str, text: str):
    """बातचीत को मेमोरी में जोड़ता है"""
    if not text or text == "None":
        return
        
    entry = {"speaker": speaker, "text": text, "ts": datetime.now().isoformat()}
    memory = load_memory_sync()
    memory["conversation"].append(entry)
    save_memory_sync(memory)

# ==============================================================================
# 3. जार्विस एक्शन फंक्शन्स (Jarvis Action Functions)
# ==============================================================================

def remember_something(memory):
    """यूजर से तथ्य पूछता है और उसे memory['facts'] में सेव करता है"""
    speak("ठीक है, मुझे क्या याद रखना है?")
    thing_to_remember = take_command()
    if thing_to_remember != "None":
        speak(f"ठीक है, '{thing_to_remember}' के बारे में क्या जानकारी याद रखनी है?")
        info = take_command()
        if info != "None":
            memory['facts'][thing_to_remember] = info
            save_memory_sync(memory)
            speak("ठीक है, मैंने यह याद कर लिया है।")
        else:
            speak("माफ़ कीजिये, मुझे जानकारी सुनाई नहीं दी।")
    else:
        speak("माफ़ कीजिये, मुझे सुनाई नहीं दिया कि क्या याद रखना है।")

def recall_something(memory, query):
    """memory['facts'] से जानकारी ढूंढकर बताता है"""
    found = False
    for key in memory['facts'].keys():
        if key in query:
            speak(f"मुझे याद है कि {key}, {memory['facts'][key]}")
            found = True
            break
    if not found:
        speak("माफ़ कीजिये, मुझे इस बारे में कोई तथ्य याद नहीं है।")

def recall_conversation(memory):
    """पिछली बातचीत को memory['conversation'] से पढ़कर सुनाता है"""
    speak("ठीक है, हमारी पिछली कुछ बातें यह हैं।")
    recent_chats = memory['conversation'][-5:] # पिछली 5 बातें
    
    if not recent_chats:
        speak("माफ़ कीजिये, अभी तक कोई बातचीत याद नहीं है।")
        return

    for entry in recent_chats:
        speaker = "आपने कहा" if entry.get("speaker") == "user" else "मैंने कहा"
        text = entry.get("text", "")
        speak(f"{speaker}, {text}")

def forget_something(memory):
    """memory['facts'] से कुछ भूलने के लिए पूछता है"""
    speak("मुझे कौन सा तथ्य भूल जाना चाहिए?")
    key_to_forget = take_command()
    if key_to_forget in memory['facts']:
        del memory['facts'][key_to_forget]
        save_memory_sync(memory)
        speak(f"ठीक है, मैं '{key_to_forget}' के बारे में भूल गया हूँ।")
    elif key_to_forget != "None":
        speak(f"मुझे '{key_to_forget}' नाम का कोई तथ्य याद नहीं है।")
    else:
        speak("माफ़ कीजिये, मुझे सुनाई नहीं दिया।")

# ==============================================================================
# 4. लाइवकिट एजेंट टूल्स (LiveKit Agent Tools) - @function_tool decorated
# ==============================================================================

@function_tool
async def load_memory(limit: int = 10) -> str:
    """मेमोरी से सभी तथ्य लोड करता है"""
    try:
        memory = load_memory_sync()
        facts = memory.get("facts", {})
        
        if not facts:
            return "अभी तक कोई तथ्य याद नहीं है।"
        
        facts_list = "\n".join([f"• {key}: {value}" for key, value in list(facts.items())[:limit]])
        return f"याद रखे गए तथ्य:\n{facts_list}"
    except Exception as e:
        return f"मेमोरी लोड करने में त्रुटि: {str(e)}"

@function_tool
async def save_memory(data: dict) -> str:
    """मेमोरी में नया डेटा सेव करता है"""
    try:
        save_memory_sync(data)
        return "✓ डेटा सफलतापूर्वक सेव हुआ"
    except Exception as e:
        return f"❌ सेव करने में त्रुटि: {str(e)}"

@function_tool
async def get_recent_conversations(limit: int = 10) -> str:
    """पिछली बातचीत को निकालता है और हिंदी में सारांश देता है"""
    try:
        memory = load_memory_sync()
        entries = memory.get("conversation", [])
        
        if not entries:
            return "अभी तक कोई बातचीत याद नहीं है।"
        
        recent = entries[-limit:]
        summary_lines = []
        
        for entry in recent:
            speaker = "आप" if entry.get("speaker") == "user" else "जार्विस"
            text = entry.get("text", "")
            summary_lines.append(f"- {speaker}: {text}")
        
        return "पिछली बातचीत:\n" + "\n".join(summary_lines)
    except Exception as e:
        return f"बातचीत निकालने में त्रुटि: {str(e)}"

@function_tool
async def add_memory_entry(speaker: str, text: str) -> str:
    """बातचीत में नई entry जोड़ता है"""
    try:
        append_conversation_sync(speaker, text)
        return f"✓ '{speaker}' की entry जोड़ी गई"
    except Exception as e:
        return f"❌ Entry जोड़ने में त्रुटि: {str(e)}"

# ==============================================================================
# 4. कमांड प्रोसेसिंग (Command Processing)
# ==============================================================================

def process_command(query, memory):
    """कमांड को प्रोसेस करता है और सही एक्शन लेता है"""
    
    if "याद रखो" in query or "याद रखना" in query:
        remember_something(memory)
        return True

    elif "पिछली बात" in query or "पिछली बातचीत" in query or "क्या बात हुई" in query:
        current_memory = load_memory_sync()
        recall_conversation(current_memory)
        return True

    elif "भूल जाओ" in query or "भूल जाना" in query:
        forget_something(memory)
        return True
    
    elif "क्या है" in query or "कब है" in query or "बताओ" in query or "कौन है" in query:
        recall_something(memory, query)
        return True

    elif "band karo" in query or "exit" in query or "stop" in query:
        speak("ठीक है, सिस्टम बंद कर रहा हूँ। अलविदा!")
        return False # लूप को रोकने के लिए False रिटर्न करें

    # अगर कोई कमांड मैच नहीं होता है
    # speak("मुझे यह कमांड समझ नहीं आया।") # आप चाहें तो इसे अनकम्मेंट कर सकते हैं
    return True # लूप जारी रखने के लिए True रिटर्न करें


# ==============================================================================
# 5. मुख्य प्रोग्राम (Main Program Execution)
# ==============================================================================

if __name__ == "__main__":
    memory_data = load_memory_sync()
    speak("सिस्टम ऑनलाइन है, मैं आपकी क्या मदद कर सकता हूँ?")
    
    # यह लूप अब बहुत साफ़ है
    while True:
        query = take_command()

        if query == "None":
            continue

        # सारा लॉजिक अब process_command फंक्शन के अंदर है
        should_continue = process_command(query, memory_data)
        
        if not should_continue:
            break
