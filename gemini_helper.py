import time
from google import genai

client = genai.Client()
MODEL = "gemini-3.8-flash"

def generate(contents, tries=5):
    for attempt in range(tries):
        try:
            response = client.models.generate_content(model=MODEL, contents=contents)
            return response.text
        except Exception as e:
            if "503" in str(e) or "429" in str(e):
                wait = 5 * (attempt + 1)
                print(f"Model busy, retrying in {wait} seconds...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("Gemini is still busy. Try again in a few minutes.")