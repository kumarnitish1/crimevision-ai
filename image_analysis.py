from google.genai import types
from gemini_helper import generate

def _ask(path, prompt):
    with open(path, "rb") as f:
        image_bytes = f.read()
    return generate([
        types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
        prompt,
    ])

def detect_objects(path):
    prompt = """You are a forensic image analyst. List what is visible, in three sections:
PEOPLE: count, clothing, posture or actions
WEAPONS: any weapon-like objects and where they are (write 'None visible' if none)
EVIDENCE: other objects that could matter to an investigation
Only report what is clearly visible."""
    return _ask(path, prompt)

def describe_scene(path):
    prompt = """You are a forensic analyst. Write:
SCENE DESCRIPTION: 3-4 sentences on location, lighting and what is happening
POSSIBLE SCENARIOS: 2-3 hypotheses about what may have occurred, each with the visible clues that support it
Treat these as possibilities, not conclusions."""
    return _ask(path, prompt)

if __name__ == "__main__":
    print("=== ACTIVITY 2.1: DETECTION ===")
    print(detect_objects("crime1.jpg"))
    print()
    print("=== ACTIVITY 2.2: SCENE AND HYPOTHESES ===")
    print(describe_scene("crime1.jpg"))