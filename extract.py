from dotenv import load_dotenv
from google import genai
from google.genai import types

from schema import Invoice

MODEL = "gemini-3.5-flash-lite"

SYSTEM_PROMPT = """You extract data from invoice images.
Rules:
- Copy every value exactly as printed. Never guess, round, or fix values.
- Identifiers (invoice number, JIB) are copied character by character, including every zero.
- Amounts are plain numbers without currency symbols (e.g. 620.00 -> 620.0).
- The date is copied as printed on the invoice.
- The currency is the code or symbol printed on the invoice (e.g. KM)."""


def extract_invoice(image_path: str) -> tuple[Invoice, types.GenerateContentResponseUsageMetadata]:
    client = genai.Client()

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    response = client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
            "Extract the data from this invoice.",
        ],
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=Invoice,
            max_output_tokens=2000,
        ),
    )

    return response.parsed, response.usage_metadata


if __name__ == "__main__":
    load_dotenv()

    invoice, usage = extract_invoice("invoices/invoice1.png")

    print(invoice.model_dump_json(indent=2))
    print()
    print("Seller JIB:", invoice.seller.jib, f"({len(invoice.seller.jib)} characters)")
    print("Buyer JIB: ", invoice.buyer.jib, f"({len(invoice.buyer.jib)} characters)")
    print("Total + 1: ", invoice.total + 1, "<- a real number, not text")
    print()
    print("Input tokens:", usage.prompt_token_count)
    print("Output tokens:", usage.candidates_token_count)
