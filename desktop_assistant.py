"""Standalone desktop voice assistant using Gemini, speech recognition, and text-to-speech."""

import os
import threading
import tkinter as tk
from tkinter import scrolledtext

import pyttsx3
import speech_recognition as sr
from dotenv import load_dotenv
from google import genai
from google.genai import types


SYSTEM_INSTRUCTION = (
    "You are NEXA, a helpful desktop AI assistant. Be clear and concise. "
    "Reply in the language the user speaks, including Telugu or English when appropriate."
)
class DesktopAssistant:
    def __init__(self, root):
        self.root = root
        self.root.title("NEXA - Desktop Voice Assistant")
        self.root.geometry("760x620")
        self.root.minsize(540, 420)
        self.root.configure(bg="#101820")

        load_dotenv()
        self.api_key = os.getenv("GOOGLE_API_KEY", "").strip()
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
        self.voice_language = os.getenv("VOICE_LANGUAGE", "en-US").strip()
        self.chat = None
        self.busy = False
        self.recognizer = sr.Recognizer()

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

    def _build_ui(self):
        header = tk.Label(
            self.root,
            text="NEXA",
            font=("Segoe UI", 28, "bold"),
            fg="#00d9ff",
            bg="#101820",
        )
        header.pack(pady=(18, 2))

        subtitle = tk.Label(
            self.root,
            text="Talk or type to start a conversation",
            font=("Segoe UI", 10),
            fg="#b8c7d1",
            bg="#101820",
        )
        subtitle.pack(pady=(0, 12))

        self.transcript = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Segoe UI", 11),
            bg="#17232d",
            fg="#f1f5f8",
            insertbackground="white",
            padx=12,
            pady=10,
            relief=tk.FLAT,
        )
        self.transcript.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 12))

        input_frame = tk.Frame(self.root, bg="#101820")
        input_frame.pack(fill=tk.X, padx=18, pady=(0, 10))

        self.message_entry = tk.Entry(
            input_frame,
            font=("Segoe UI", 11),
            bg="#17232d",
            fg="#f1f5f8",
            insertbackground="white",
            relief=tk.FLAT,
        )
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=9, padx=(0, 8))
        self.message_entry.bind("<Return>", self._send_typed_message)

        self.send_button = tk.Button(
            input_frame,
            text="Send",
            command=self._send_typed_message,
            bg="#087e8b",
            fg="white",
            activebackground="#0a9aa8",
            activeforeground="white",
            relief=tk.FLAT,
            padx=16,
            pady=8,
        )
        self.send_button.pack(side=tk.RIGHT)

        controls = tk.Frame(self.root, bg="#101820")
        controls.pack(fill=tk.X, padx=18, pady=(0, 8))

        self.listen_button = tk.Button(
            controls,
            text="Listen",
            command=self._listen,
            bg="#146c43",
            fg="white",
            activebackground="#198754",
            activeforeground="white",
            relief=tk.FLAT,
            padx=18,
            pady=8,
        )
        self.listen_button.pack(side=tk.LEFT)

        self.new_chat_button = tk.Button(
            controls,
            text="New chat",
            command=self._new_chat,
            bg="#34495e",
            fg="white",
            activebackground="#425d78",
            activeforeground="white",
            relief=tk.FLAT,
            padx=14,
            pady=8,
        )
        self.new_chat_button.pack(side=tk.LEFT, padx=(8, 0))

        self.status = tk.StringVar(value="Ready")
        status_label = tk.Label(
            self.root,
            textvariable=self.status,
            anchor=tk.W,
            font=("Segoe UI", 9),
            fg="#b8c7d1",
            bg="#101820",
        )
        status_label.pack(fill=tk.X, padx=20, pady=(0, 12))

    def _append_message(self, speaker, text):
        self.transcript.configure(state=tk.NORMAL)
        self.transcript.insert(tk.END, f"{speaker}: {text}\n\n")
        self.transcript.see(tk.END)
        self.transcript.configure(state=tk.DISABLED)

    def _set_busy(self, busy, status):
        self.busy = busy
        self.status.set(status)
        state = tk.DISABLED if busy else tk.NORMAL
        self.listen_button.configure(state=state)
        self.send_button.configure(state=state)
        self.message_entry.configure(state=state)
        self.new_chat_button.configure(state=state)
        if not busy:
            self.message_entry.focus_set()

    def _start_task(self, task, status):
        if self.busy:
            return
        self._set_busy(True, status)
        threading.Thread(target=task, daemon=True).start()

    def _listen(self):
        self._start_task(self._listen_and_respond, "Listening for speech...")

    def _listen_and_respond(self):
        try:
            self.root.after(0, lambda: self.status.set("Adjusting microphone..."))
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                self.root.after(0, lambda: self.status.set("Listening..."))
                audio = self.recognizer.listen(
                    source,
                    timeout=5,
                    phrase_time_limit=20,
                )
            self.root.after(0, lambda: self.status.set("Transcribing speech..."))
            message = self.recognizer.recognize_google(
                audio,
                language=self.voice_language,
            )
            self._respond(message)
        except sr.WaitTimeoutError:
            self._show_error("I didn't hear anything. Press Listen and try again.")
        except sr.UnknownValueError:
            self._show_error("I couldn't understand that. Please try again.")
        except sr.RequestError as error:
            self._show_error(f"Speech recognition service error: {error}")
        except Exception as error:
            self._show_error(f"Voice assistant error: {error}")
        finally:
            self.root.after(0, lambda: self._set_busy(False, "Ready"))

    def _send_typed_message(self, event=None):
        message = self.message_entry.get().strip()
        if not message or self.busy:
            return "break"
        self.message_entry.delete(0, tk.END)
        self._start_task(lambda: self._respond_and_finish(message), "Thinking...")
        return "break"

    def _respond_and_finish(self, message):
        try:
            self._respond(message)
        finally:
            self.root.after(0, lambda: self._set_busy(False, "Ready"))

    def _respond(self, message):
        self.root.after(0, lambda: self._append_message("You", message))
        try:
            if not self.api_key:
                raise ValueError(
                    "GOOGLE_API_KEY is missing. Add it to the .env file and restart."
                )
            if self.chat is None:
                client = genai.Client(api_key=self.api_key)
                self.chat = client.chats.create(
                    model=self.model_name,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                    ),
                )

            self.root.after(0, lambda: self.status.set("Generating a response..."))
            response = self.chat.send_message(message)
            reply = response.text
            if not reply:
                raise RuntimeError("Gemini returned an empty response.")

            self.root.after(0, lambda: self._append_message("NEXA", reply))
            self.root.after(0, lambda: self.status.set("Speaking..."))
            engine = pyttsx3.init()
            engine.say(reply)
            engine.runAndWait()
            engine.stop()
        except Exception as error:
            self._show_error(f"Assistant error: {error}")

    def _show_error(self, message):
        self.root.after(0, lambda: self._append_message("Error", message))
        self.root.after(0, lambda: self.status.set(message))

    def _new_chat(self):
        if self.busy:
            return
        self.chat = None
        self.transcript.configure(state=tk.NORMAL)
        self.transcript.delete("1.0", tk.END)
        self.transcript.configure(state=tk.DISABLED)
        self.status.set("New chat started")


def main():
    root = tk.Tk()
    DesktopAssistant(root)
    root.mainloop()


if __name__ == "__main__":
    main()
