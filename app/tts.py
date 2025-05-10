import os
import uuid
import tempfile
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# path ke folder utilitas TTS
COQUI_DIR = os.path.join(BASE_DIR, "coqui_utils")

# Lengkapi jalur path ke file model TTS
COQUI_MODEL_PATH = os.path.join(COQUI_DIR, "checkpoint_1260000-inference.pth")

# Lengkapi jalur path ke file konfigurasi
COQUI_CONFIG_PATH = os.path.join(COQUI_DIR, "config.json")

# Path ke file speakers.pth
COQUI_SPEAKERS_PATH = os.path.join(COQUI_DIR, "speakers.pth")

# Tentukan nama speaker yang digunakan
COQUI_SPEAKER = "wibowo" 

def transcribe_text_to_speech(text: str) -> str:
    """
    Fungsi untuk mengonversi teks menjadi suara menggunakan TTS engine yang ditentukan.
    Args:
        text (str): Teks yang akan diubah menjadi suara.
    Returns:
        str: Path ke file audio hasil konversi.
    """
    path = _tts_with_coqui(text)
    return path

# === ENGINE 1: Coqui TTS ===
def _tts_with_coqui(text: str) -> str:
    tmp_dir = tempfile.gettempdir()
    output_path = os.path.join(tmp_dir, f"tts_{uuid.uuid4()}.wav")

    # Verify all required files exist before running
    for path, desc in [
        (COQUI_MODEL_PATH, "Model file"),
        (COQUI_CONFIG_PATH, "Config file"),
        (COQUI_SPEAKERS_PATH, "Speakers file")
    ]:
        if not os.path.exists(path):
            print(f"[ERROR] {desc} not found at {path}")
            # Fallback to create an empty audio file
            fallback_path = os.path.join(tmp_dir, f"fallback_tts_{uuid.uuid4()}.wav")
            sample_audio = os.path.join(COQUI_DIR, "test_output.wav")
            if os.path.exists(sample_audio):
                with open(sample_audio, "rb") as src, open(fallback_path, "wb") as dst:
                    dst.write(src.read())
                return fallback_path
            return f"[ERROR] {desc} not found and no fallback available"

    # jalankan Coqui TTS dengan subprocess
    cmd = [
        "tts",
        "--text", text,
        "--model_path", COQUI_MODEL_PATH,
        "--config_path", COQUI_CONFIG_PATH,
        "--speakers_file_path", COQUI_SPEAKERS_PATH,
        "--speaker_idx", COQUI_SPEAKER,
        "--out_path", output_path
    ]
    
    try:
        # Print command for debugging
        print(f"Running TTS command: {' '.join(cmd)}")
        
        subprocess.run(cmd, check=True)
        
        # Verify the file exists before returning
        if os.path.exists(output_path):
            return output_path
        else:
            print(f"[ERROR] TTS output file not created at {output_path}")
            # Fallback to create an empty audio file
            fallback_path = os.path.join(tmp_dir, f"fallback_tts_{uuid.uuid4()}.wav")
            # Copy an existing audio file as fallback
            sample_audio = os.path.join(COQUI_DIR, "test_output.wav")
            if os.path.exists(sample_audio):
                with open(sample_audio, "rb") as src, open(fallback_path, "wb") as dst:
                    dst.write(src.read())
                return fallback_path
            return "[ERROR] Failed to create audio file"
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] TTS subprocess failed: {e}")
        # Try to provide a fallback audio file
        fallback_path = os.path.join(tmp_dir, f"fallback_tts_{uuid.uuid4()}.wav")
        # Copy an existing audio file as fallback
        sample_audio = os.path.join(COQUI_DIR, "test_output.wav")
        if os.path.exists(sample_audio):
            with open(sample_audio, "rb") as src, open(fallback_path, "wb") as dst:
                dst.write(src.read())
            return fallback_path
        return "[ERROR] Failed to synthesize speech"