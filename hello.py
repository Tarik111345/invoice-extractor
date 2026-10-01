from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()
client = genai.Client()

response = client.models.generate_content(
    model="gemini-3.5-flash-lite",
    contents="What must a valid invoice in Bosnia and Herzegovina contain?",
    config=types.GenerateContentConfig(
        system_instruction="You are an experienced accountant from Sarajevo. Answer briefly and clearly.",
        max_output_tokens=200,
    ),
)
print(response.text)
print("Input tokens:", response.usage_metadata.prompt_token_count)
print("Output tokens:", response.usage_metadata.candidates_token_count)
print("Total tokens:", response.usage_metadata.total_token_count)
