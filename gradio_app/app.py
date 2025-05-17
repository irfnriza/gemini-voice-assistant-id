# file app.py

import os
import tempfile
import json
import time
import requests
import gradio as gr
import scipy.io.wavfile
import logging
from typing import Dict, Tuple, Optional, Any, List
import configparser
import ast

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("voice_chatbot_ui.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("voice-chatbot-ui")

# Load configuration or set defaults
config = configparser.ConfigParser()
config['DEFAULT'] = {
    'api_url': 'http://localhost:8000',
    'max_logs': '10'
}

CONFIG_FILE = 'voice_chatbot_config.ini'
if os.path.exists(CONFIG_FILE):
    config.read(CONFIG_FILE)

API_URL = config['DEFAULT']['api_url']
MAX_LOGS = int(config['DEFAULT']['max_logs'])

# Global variables to store conversation history and logs
conversation_history = []
process_logs = []

def save_config():
    """Save current configuration to file"""
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)

def check_api_status() -> Dict[str, Any]:
    """Check if the API server is running and get component status"""
    try:
        response = requests.get(f"{API_URL}/status", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return {"api": "error", "message": f"API returned status code {response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"api": "error", "message": f"Could not connect to API: {str(e)}"}

def format_process_info(process_info: str) -> str:
    """Format process info from API response header for display"""
    try:
        # Convert string representation of dict to actual dict
        data = ast.literal_eval(process_info)
        
        # Format as markdown for display
        md = "### Processing Information\n\n"
        md += f"**Transcribed Text:** {data.get('transcribed_text', 'N/A')}\n\n"
        md += f"**AI Response:** {data.get('ai_response', 'N/A')}\n\n"
        
        # Add timing information
        md += "**Processing Times:**\n"
        for step, time_taken in data.get('process_times', {}).items():
            md += f"- {step.replace('_', ' ').title()}: {time_taken}\n"
        
        md += f"\n**Total Processing Time:** {data.get('total_process_time', 'N/A')}s\n"
        
        return md
    except Exception as e:
        logger.error(f"Error formatting process info: {e}")
        return f"Error parsing processing info: {str(e)}"

def voice_chat(audio, api_url_input) -> Tuple[Optional[str], str, str]:
    """
    Send voice to API and get response
    
    Args:
        audio: Gradio audio input (sample_rate, data)
        api_url_input: API URL from the UI
    
    Returns:
        Tuple containing:
        - Audio response path (or None if error)
        - Status message for UI
        - Log output for UI
    """
    global process_logs, API_URL
    
    # Update API URL if changed
    if api_url_input != API_URL:
        API_URL = api_url_input
        config['DEFAULT']['api_url'] = API_URL
        save_config()
        logger.info(f"Updated API URL to {API_URL}")
    
    if audio is None:
        return None, "❌ No audio recorded", "Please record audio first"
    
    sr, audio_data = audio
    
    # Add timestamp to logs
    log_entry = f"--- {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n"
    
    try:
        # Save as .wav
        log_entry += "Saving temporary audio file...\n"
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:
            scipy.io.wavfile.write(tmpfile.name, sr, audio_data)
            audio_path = tmpfile.name
            log_entry += f"Audio saved to {audio_path}\n"
        
        # Send to FastAPI endpoint
        log_entry += f"Sending request to API at {API_URL}/voice-chat...\n"
        start_time = time.time()
        
        with open(audio_path, "rb") as f:
            files = {"audio": ("voice.wav", f, "audio/wav")}
            response = requests.post(f"{API_URL}/voice-chat", files=files)
        
        request_time = time.time() - start_time
        log_entry += f"Request completed in {request_time:.2f} seconds\n"
        
        # Process response
        if response.status_code == 200:
            # Extract process info from headers
            process_info = response.headers.get('X-Process-Info', '{}')
            formatted_info = format_process_info(process_info)
            
            # Save response audio
            output_audio_path = os.path.join(tempfile.gettempdir(), f"tts_output_{int(time.time())}.wav")
            with open(output_audio_path, "wb") as f:
                f.write(response.content)
            
            log_entry += f"Response saved to {output_audio_path}\n"
            log_entry += "Processing completed successfully ✅\n"
            
            # Clean up input file
            os.unlink(audio_path)
            
            # Add to process logs
            process_logs.append(log_entry)
            if len(process_logs) > MAX_LOGS:
                process_logs = process_logs[-MAX_LOGS:]
            
            return output_audio_path, "✅ Response received", formatted_info
        else:
            error_msg = f"❌ API Error ({response.status_code}): {response.text}"
            log_entry += f"{error_msg}\n"
            process_logs.append(log_entry)
            return None, error_msg, log_entry
    
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        log_entry += f"{error_msg}\n"
        process_logs.append(log_entry)
        logger.error(f"Error in voice_chat: {e}", exc_info=True)
        return None, error_msg, log_entry

def check_connection(api_url_input) -> str:
    """Check connection to API server"""
    global API_URL
    
    # Update API URL if changed
    if api_url_input != API_URL:
        API_URL = api_url_input
        config['DEFAULT']['api_url'] = API_URL
        save_config()
    
    status = check_api_status()
    
    if status.get('api') == 'online':
        components = status.get('components', {})
        
        # Create status message
        message = "### 🟢 API Connected\n\n"
        message += "**Component Status:**\n"
        
        for component, info in components.items():
            icon = "✅" if info.get('status') == 'ok' else "❌"
            message += f"- **{component.upper()}**: {icon} {info.get('message', '')}\n"
            
        return message
    else:
        return f"### 🔴 API Disconnected\n\n**Error:** {status.get('message', 'Unknown error')}"

def clear_logs():
    """Clear process logs"""
    global process_logs
    process_logs = []
    return "Logs cleared."

def get_combined_logs() -> str:
    """Get all logs as a single string"""
    return "\n".join(process_logs)

def refresh_logs():
    """Manual refresh for logs"""
    return get_combined_logs()

# Custom CSS for a more elegant UI
custom_css = """
.main-container {
    max-width: 1000px;
    margin: 0 auto;
}
.status-indicator {
    padding: 5px 10px;
    border-radius: 15px;
    display: inline-block;
    font-weight: bold;
}
.online {
    background-color: rgba(0, 255, 0, 0.2);
    color: #006400;
}
.offline {
    background-color: rgba(255, 0, 0, 0.2);
    color: #8B0000;
}
.header-content {
    text-align: center;
    margin-bottom: 20px;
}
.footer {
    margin-top: 30px;
    text-align: center;
    font-size: 0.8em;
    color: #888;
}
"""

# UI Gradio
with gr.Blocks(theme=gr.themes.Soft(), css=custom_css) as demo:
    with gr.Row(elem_classes="header-content"):
        gr.Markdown("# 🎙️ Voice Chatbot")
        gr.Markdown("Berbicara langsung ke mikrofon dan dapatkan jawaban suara dari asisten AI.")
    
    # Main chat interface (visible by default)
    with gr.Row():
        with gr.Column(scale=1):
            audio_input = gr.Audio(
                sources="microphone", 
                type="numpy",
                label="🎤 Rekam Pertanyaan Anda"
            )
            submit_btn = gr.Button("🔁 Submit", variant="primary", size="lg")
            status_box = gr.Textbox(label="Status", value="Siap menerima input suara")
        
        with gr.Column(scale=1):
            audio_output = gr.Audio(
                type="filepath",
                label="🔊 Balasan dari Asisten"
            )
            process_info = gr.Markdown("### Detail Proses\nAkan muncul setelah respons diterima")
    
    # Advanced settings in collapsible section
    with gr.Accordion("Advanced Settings", open=False):
        with gr.Row():
            with gr.Column(scale=2):
                api_url_input = gr.Textbox(
                    label="API URL", 
                    value=API_URL,
                    info="URL API server voice chatbot"
                )
            with gr.Column(scale=1):
                check_btn = gr.Button("🔄 Check Connection")
                
        connection_status = gr.Markdown("### Status koneksi belum diperiksa")
        
        # Logs in nested accordion
        with gr.Accordion("System Logs", open=False):
            with gr.Row():
                clear_logs_btn = gr.Button("🗑️ Clear Logs")
                refresh_logs_btn = gr.Button("🔄 Refresh Logs")
                
            process_log_output = gr.Textbox(
                label="Process Logs", 
                value="Logs akan muncul di sini", 
                lines=10,
                max_lines=20
            )
    
    # Footer
    with gr.Row(elem_classes="footer"):
        gr.Markdown("© 2025 Voice Chatbot System")
            
    # Connect the UI elements to functions
    submit_btn.click(
        fn=voice_chat,
        inputs=[audio_input, api_url_input],
        outputs=[audio_output, status_box, process_info]
    )
    
    check_btn.click(
        fn=check_connection,
        inputs=api_url_input,
        outputs=connection_status
    )
    
    clear_logs_btn.click(
        fn=clear_logs,
        inputs=[],
        outputs=process_log_output
    )
    
    refresh_logs_btn.click(
        fn=refresh_logs,
        inputs=[],
        outputs=process_log_output
    )
    
    # Check connection on load but without blocking UI
    demo.load(
        fn=check_connection,
        inputs=[api_url_input],
        outputs=connection_status
    )

if __name__ == "__main__":
    demo.launch()