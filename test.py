from google import genai

client = genai.Client()
r = client.models.generate_content(model="gemini-3.8-flash", contents="Say hello in one line")
print(r.text)