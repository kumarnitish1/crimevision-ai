
import time
from google import genai
from google.genai import types

client = genai.Client(
    http_options=types.HttpOptions(timeout=30000)
)

MODEL = MODEL = "gemini-3.5-flash"

def generate(contents, tries=3):
    for attempt in range(tries):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=contents
            )
            return response.text

        except Exception as e:
            error = str(e)
            if "503" in error or "429" in error:
                wait = 5 * (attempt + 1)
                print(f"Model busy. Retrying in {wait} seconds...")
                time.sleep(wait)
            else:
                raise

    raise RuntimeError(
        "Gemini remained busy after 3 attempts. Try again later."
    )
