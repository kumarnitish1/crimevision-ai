import os
from google.genai import types
from gemini_helper import generate

MIME_TYPES = {
    ".mp3": "audio/mp3",
    ".wav": "audio/wav",
    ".m4a": "audio/mp4",
    ".aac": "audio/aac",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
}

def _ask_audio(path, prompt):
    ext = os.path.splitext(path)[1].lower()
    mime = MIME_TYPES.get(ext, "audio/mp3")
    with open(path, "rb") as f:
        audio_bytes = f.read()
    return generate([
        types.Part.from_bytes(data=audio_bytes, mime_type=mime),
        prompt,
    ])

def transcribe_audio(path):
    prompt = "Transcribe this audio word for word. Output only the transcript."
    return _ask_audio(path, prompt)

def analyze_statement(path):
    prompt = """You are a forensic audio analyst. Listen to this witness statement and report:
TRANSCRIPT: the full text
KEY FACTS: people, places, times, objects and actions mentioned
TONE: the speaker's emotional state (calm, stressed, hesitant)
GAPS: details that are unclear or missing and worth asking about
Only report what is actually said."""
    return _ask_audio(path, prompt)




if __name__ == "__main__":
    try:
        transcript = transcribe_audio("witness.m4a")
        print("=== WITNESS TRANSCRIPT ===")
        print(transcript)

        analysis = analyze_statement("witness.m4a")
        print("\n=== WITNESS STATEMENT ANALYSIS ===")
        print(analysis)

        with open("audio_results.txt", "w", encoding="utf-8") as file:
            file.write("WITNESS TRANSCRIPT\n")
            file.write(transcript)
            file.write("\n\nWITNESS STATEMENT ANALYSIS\n")
            file.write(analysis)

        print("\nSaved audio analysis to audio_results.txt")

    except Exception as error:
        print(f"Audio analysis failed: {error}")
