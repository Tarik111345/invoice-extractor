import json
import random
from datetime import date, timedelta
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from schema import Invoice, LineItem, Party

OUTPUT_DIR = Path("invoices/eval")
ANSWERS_FILE = OUTPUT_DIR / "answers.json"
INVOICE_COUNT = 20
SEED = 42
VAT_RATE = 0.17
FONT_PATH = "C:/Windows/Fonts/arial.ttf"

COMPANIES = [
    "Test Ltd. Sarajevo",
    "Demo Ltd. Mostar",
    "Bosna Soft d.o.o. Tuzla",
    "Neretva Trade d.o.o. Mostar",
    "Una Digital d.o.o. Bihac",
    "Drina Logistics d.o.o. Zvornik",
    "Sana Consulting d.o.o. Sanski Most",
    "Vrbas Print d.o.o. Banja Luka",
]

PRODUCTS = [
    ("Web design", 300, 1500),
    ("Hosting (12 mo)", 60, 240),
    ("Domain registration", 15, 40),
    ("SEO audit", 200, 800),
    ("Logo design", 150, 600),
    ("IT support (hours)", 30, 60),
    ("Office chair", 120, 450),
    ("Laptop", 900, 2500),
    ("Printer toner", 40, 120),
    ("Consulting (hours)", 50, 120),
]


def random_jib(rng: random.Random) -> str:
    # Every other JIB is "hard": long runs of zeros, the case where Gemini dropped a digit.
    if rng.random() < 0.5:
        return "4" + "0" * 11 + str(rng.randint(0, 9))
    return "4" + "".join(str(rng.randint(0, 9)) for _ in range(12))


def random_invoice(rng: random.Random, number: int) -> Invoice:
    seller_name, buyer_name = rng.sample(COMPANIES, 2)

    items = []
    for description, low, high in rng.sample(PRODUCTS, rng.randint(1, 5)):
        quantity = float(rng.randint(1, 10))
        unit_price = round(rng.uniform(low, high), 2)
        items.append(
            LineItem(
                description=description,
                quantity=quantity,
                unit_price=unit_price,
                amount=round(quantity * unit_price, 2),
            )
        )

    subtotal = round(sum(item.amount for item in items), 2)
    vat = round(subtotal * VAT_RATE, 2)
    invoice_date = date(2026, 1, 1) + timedelta(days=rng.randint(0, 280))

    return Invoice(
        invoice_number=f"2026-{number:03d}",
        date=invoice_date.strftime("%d.%m.%Y"),
        seller=Party(name=seller_name, jib=random_jib(rng)),
        buyer=Party(name=buyer_name, jib=random_jib(rng)),
        items=items,
        subtotal=subtotal,
        vat=vat,
        total=round(subtotal + vat, 2),
        currency="KM",
    )


def draw_invoice(invoice: Invoice, path: Path) -> None:
    font = ImageFont.truetype(FONT_PATH, 16)
    bold = ImageFont.truetype(FONT_PATH.replace("arial", "arialbd"), 16)

    height = 330 + 24 * len(invoice.items)
    image = Image.new("RGB", (640, height), "white")
    draw = ImageDraw.Draw(image)

    def text(x: int, y: int, value: str, f=font) -> None:
        draw.text((x, y), value, fill="black", font=f)

    def right(x: int, y: int, value: str) -> None:
        draw.text((x, y), value, fill="black", font=font, anchor="ra")

    text(20, 20, f"INVOICE No. {invoice.invoice_number}", bold)
    right(620, 20, f"Date: {invoice.date}")
    text(20, 50, f"Seller: {invoice.seller.name}, JIB: {invoice.seller.jib}")
    text(20, 74, f"Buyer:  {invoice.buyer.name}, JIB: {invoice.buyer.jib}")

    y = 120
    text(20, y, "Item", bold)
    right(380, y, "Qty")
    right(500, y, "Unit price")
    right(620, y, "Amount")
    draw.line((20, y + 22, 620, y + 22), fill="black")

    for item in invoice.items:
        y += 28
        text(20, y, item.description)
        right(380, y, f"{item.quantity:g}")
        right(500, y, f"{item.unit_price:.2f}")
        right(620, y, f"{item.amount:.2f}")

    y += 40
    draw.line((360, y - 8, 620, y - 8), fill="black")
    text(380, y, "Subtotal:")
    right(620, y, f"{invoice.subtotal:.2f} {invoice.currency}")
    text(380, y + 24, "VAT 17%:")
    right(620, y + 24, f"{invoice.vat:.2f} {invoice.currency}")
    text(380, y + 48, "TOTAL:", bold)
    right(620, y + 48, f"{invoice.total:.2f} {invoice.currency}")

    image.save(path)


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)

    answers = {}
    for number in range(1, INVOICE_COUNT + 1):
        invoice = random_invoice(rng, number)
        filename = f"invoice_{number:02d}.png"
        draw_invoice(invoice, OUTPUT_DIR / filename)
        answers[filename] = invoice.model_dump()

    ANSWERS_FILE.write_text(json.dumps(answers, indent=2), encoding="utf-8")
    print(f"Generated {INVOICE_COUNT} invoices and {ANSWERS_FILE}")
