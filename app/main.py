# file main.py

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import shutil
import tempfile
import uuid
import os
import time
import logging
from typing import List, Dict, Any

from stt import transcribe_speech_to_text
from llm import generate_response
from tts import transcribe_text_to_speech

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("api_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("voice-chatbot")

app = FastAPI(title="Voice Chatbot API")

ALLOWED_AUDIO_EXTENSIONS = [".wav", ".mp3", ".ogg", ".m4a"]
TEMP_FILES = []  # Track temporary files to clean up later

@app.on_event("shutdown")
async def cleanup_temp_files():
    """Clean up any temporary files when the server shuts down"""
    for file_path in TEMP_FILES:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Cleaned up temp file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to clean up {file_path}: {e}")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "online", "message": "Voice Chatbot API is running"}

@app.post("/voice-chat")
async def voice_chat(audio: UploadFile = File(...)):
    """
    Process voice input and return audio response
    
    Args:
        audio (UploadFile): The uploaded audio file
    
    Returns:
        FileResponse: The audio response file
    """
    process_times = {}
    response_data = {}
    
    # Validate file format
    file_ext = os.path.splitext(audio.filename)[1].lower()
    if file_ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported audio format. Allowed formats: {', '.join(ALLOWED_AUDIO_EXTENSIONS)}"
        )
    
    # Create a temporary directory for processing
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Save uploaded audio to temp file
        start_time = time.time()
        temp_audio_path = os.path.join(tmpdir, f"{uuid.uuid4()}{file_ext}")
        
        try:
            with open(temp_audio_path, "wb") as buffer:
                shutil.copyfileobj(audio.file, buffer)
            process_times["save_audio"] = f"{(time.time() - start_time):.3f}s"
            logger.info(f"Audio saved to {temp_audio_path}")
        except Exception as e:
            logger.error(f"Failed to save audio: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to process audio: {str(e)}")

        # 2. Speech-to-Text
        start_time = time.time()
        try:
            with open(temp_audio_path, "rb") as audio_file:
                audio_bytes = audio_file.read()
            user_text = transcribe_speech_to_text(audio_bytes, file_ext=file_ext)
            process_times["speech_to_text"] = f"{(time.time() - start_time):.3f}s"
            response_data["transcribed_text"] = user_text
            logger.info(f"Transcribed text: {user_text}")
        except Exception as e:
            error_msg = f"Speech-to-text failed: {str(e)}"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)

        # 3. Generate response from LLM
        start_time = time.time()
        try:
            ai_response = generate_response(user_text.strip())
            process_times["llm_response"] = f"{(time.time() - start_time):.3f}s"
            response_data["ai_response"] = ai_response
            logger.info(f"AI Response: {ai_response}")
        except Exception as e:
            error_msg = f"LLM processing failed: {str(e)}"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)

        # 4. Text-to-Speech
        start_time = time.time()
        try:
            audio_output_path = transcribe_text_to_speech(ai_response)
            TEMP_FILES.append(audio_output_path)  # Track for cleanup
            process_times["text_to_speech"] = f"{(time.time() - start_time):.3f}s"
            logger.info(f"TTS output saved to {audio_output_path}")
        except Exception as e:
            error_msg = f"Text-to-speech failed: {str(e)}"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)

    # Calculate total process time
    response_data["process_times"] = process_times
    response_data["total_process_time"] = sum(float(t.rstrip('s')) for t in process_times.values())
    
    # Return both the audio file and processing metadata as headers
    headers = {"X-Process-Info": f"{response_data}"}
    
    # Return the audio file with processing metadata
    return FileResponse(
        path=audio_output_path,
        media_type="audio/wav",
        filename="response.wav",
        headers=headers
    )

@app.get("/status")
async def get_status():
    """Get API status and components health"""
    status = {
        "api": "online",
        "components": {
            "stt": check_stt_health(),
            "llm": check_llm_health(),
            "tts": check_tts_health()
        }
    }
    return JSONResponse(content=status)

def check_stt_health() -> Dict[str, Any]:
    """Check STT component health"""
    try:
        # Basic check if whisper binary exists
        from stt import WHISPER_BINARY
        exists = os.path.exists(WHISPER_BINARY)
        return {"status": "ok" if exists else "error", "message": f"Binary exists: {exists}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def check_llm_health() -> Dict[str, Any]:
    """Check LLM component health"""
    try:
        # Check if API key is set
        from llm import GOOGLE_API_KEY
        has_key = bool(GOOGLE_API_KEY)
        return {"status": "ok" if has_key else "error", "message": "API key configured" if has_key else "API key missing"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def check_tts_health() -> Dict[str, Any]:
    """Check TTS component health"""
    try:
        # Check if model exists
        from tts import COQUI_MODEL_PATH
        exists = os.path.exists(COQUI_MODEL_PATH)
        return {"status": "ok" if exists else "error", "message": f"Model exists: {exists}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}