
from gemini_helper import generate

if __name__ == "__main__":
    print("Testing Gemini API...")

    try:
        response = generate("Say hello in one line.")
        print("Gemini response:")
        print(response)
    except Exception as e:
        print("Gemini API test failed:")
        print(e)
