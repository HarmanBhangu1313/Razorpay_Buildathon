from google import genai
import os
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6Kve9bBOcaO4JkCqEr9BhwGGyVywK3NMF5V2bu9U4jcZQ"))
for model in client.models.list():
    print(model.name)
