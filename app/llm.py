# file llm.py 

import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

MODEL = "gemini-1.5-flash"  # Model Gemini yang digunakan

# Ambil API key dari .env
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHAT_HISTORY_FILE = os.path.join(BASE_DIR, "chat_history.json")

# Instruksi sistem untuk AI
system_instruction = """
You are a responsive, intelligent, and fluent virtual assistant who communicates in Indonesian.
Your task is to provide clear, concise, and informative answers in response to user queries or statements spoken through voice.

Your answers must:
- Be written in polite and easily understandable Indonesian.
- Be short and to the point (maximum 2–3 sentences).
- Avoid repeating the user's question; respond directly with the answer.

Example tone:
User: Cuaca hari ini gimana?
Assistant: Hari ini cuacanya cerah di sebagian besar wilayah, dengan suhu sekitar 30 derajat.

User: Kamu tahu siapa presiden Indonesia?
Assistant: Presiden Indonesia saat ini adalah Joko Widodo.

If you're unsure about an answer, be honest and say that you don't know.
"""

# Konfigurasi dan inisialisasi model
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(model_name=MODEL, system_instruction=system_instruction)

def save_chat_history(history):
    try:
        with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[ERROR] Gagal menyimpan riwayat chat: {e}")

def load_chat_history():
    if not os.path.exists(CHAT_HISTORY_FILE) or os.path.getsize(CHAT_HISTORY_FILE) == 0:
        return model.start_chat(history=[])

    try:
        with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
            return model.start_chat(history=history)
    except Exception as e:
        print(f"[ERROR] Gagal memuat riwayat chat: {e}")
        return model.start_chat(history=[])

chat = load_chat_history()

def generate_response(prompt: str) -> str:
    try:
        response = chat.send_message(prompt)
        save_chat_history(chat.history)
        return response.text or "[ERROR] No response from model"
    except Exception as e:
        return f"[ERROR] {str(e)}"

# Untuk pengujian langsung
if __name__ == "__main__":
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            break
        response = generate_response(user_input)
        print("Assistant:", response)
