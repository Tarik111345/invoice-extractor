from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client()

with open("invoices/invoice1.png", "rb") as f:
    image_bytes = f.read()

image = types.Part.from_bytes(data=image_bytes, mime_type="image/png")

response = client.models.generate_content(
    model="gemini-3.5-flash-lite",
    contents=[image, "Read this invoice and list all the data you see."],
    config=types.GenerateContentConfig(
        system_instruction="You are an assistant that reads invoices. Extract data exactly as written. Never guess.",
        max_output_tokens=1000,
    ),
)

print(response.text)
print("Input tokens:", response.usage_metadata.prompt_token_count)
print("Output tokens:", response.usage_metadata.candidates_token_count)
print("Total tokens:", response.usage_metadata.total_token_count)