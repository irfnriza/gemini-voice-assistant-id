# 🎙️ Voice Chatbot System

A complete voice-based AI assistant that allows users to speak directly to an AI and receive spoken responses in return.

## 📝 Project Overview

This project implements a voice interaction pipeline consisting of three main components:
- **Speech-to-Text (STT)**: Converting user's voice input to text
- **Language Model (LLM)**: Processing the text input and generating responses
- **Text-to-Speech (TTS)**: Converting the AI's text response back to speech

The system is architected with a separate backend API (FastAPI) and frontend UI (Gradio), enabling flexible deployment options.

## 🔧 Technology Stack

### Backend (main.py)
- **FastAPI**: RESTful API framework handling audio processing pipeline
- **Whisper.cpp**: Efficient speech recognition for transcribing user audio
- **Google Gemini API**: Large Language Model for generating responses
- **Coqui TTS**: Text-to-speech synthesis for natural-sounding responses

### Frontend (app.py)
- **Gradio**: Web-based UI for voice interaction
- **Bilingual Support**: Interface available in both English and Indonesian
- **Process Monitoring**: Real-time logs and performance metrics

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- FFmpeg (for audio processing)
- Whisper.cpp installed
- Google API Key for Gemini API
- Coqui TTS model

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/voice-chatbot.git
cd voice-chatbot
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Create a .env file with required API keys and paths
```
GOOGLE_API_KEY=your_google_api_key
WHISPER_BINARY=/path/to/whisper/binary
COQUI_MODEL_PATH=/path/to/coqui/model
```

### Running the Application

1. Start the backend server
```bash
python main.py
```

2. In another terminal, start the frontend
```bash
python app.py
```

3. Open your browser and navigate to the URL shown in the terminal (typically http://127.0.0.1:7860)

## 🔄 Usage Flow

1. Click the microphone button and speak your question
2. The system will:
   - Convert your speech to text using Whisper
   - Process the text through the Gemini API
   - Convert the response to speech using Coqui TTS
   - Play back the audio response

## 🛠️ Project Structure

```
voice_chatbot_project/
│
├── app/
│   ├── main.py            # Endpoint utama FastAPI
│   ├── llm.py             # Integrasi Gemini API
│   ├── stt.py             # Transkripsi suara (whisper.cpp)
│   ├── tts.py             # TTS dengan Coqui
│   └── whisper.cpp/       # Hasil clone whisper.cpp
│   └── coqui_utils/       # Model dan config Coqui TTS
│
├── gradio_app/
│   └── app.py             # Frontend dengan Gradio
│
├── .env                   # Menyimpan Gemini API Key
├── requirements.txt       # Daftar dependensi Python
```

## 📊 Performance Considerations

The system logs detailed performance metrics for each processing stage:
- Speech-to-text transcription time
- LLM response generation time
- Text-to-speech synthesis time
- Total processing time

These metrics help identify bottlenecks and optimization opportunities.

## 🔍 Challenges and Solutions

### Integration Complexity
- **Challenge**: Connecting three separate AI models (STT, LLM, TTS) with different input/output formats
- **Solution**: Created a modular architecture with clear interfaces between components

### Latency Management
- **Challenge**: Multi-step processing pipeline introduced significant latency
- **Solution**: Implemented asynchronous processing where possible and optimized data passing between components

### Debugging Across Components
- **Challenge**: Difficulty in tracking errors across the complete pipeline
- **Solution**: Implemented comprehensive logging system with detailed process information

## 🔮 Future Improvements

- Add conversation memory to maintain context across interactions
- Implement streaming responses for lower perceived latency
- Support additional languages beyond English and Indonesian
- Add voice fingerprinting for multi-user support

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Related Links

- [Whisper.cpp](https://github.com/ggerganov/whisper.cpp)
- [Google Gemini API](https://ai.google.dev/docs/gemini_api)
- [Coqui TTS](https://github.com/coqui-ai/TTS)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Gradio](https://www.gradio.app/)
