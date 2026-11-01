from datetime import date, datetime

from schema import Invoice, Party

VAT_RATE = 0.17
JIB_LENGTH = 13
MONEY_TOLERANCE = 0.01
DATE_FORMAT = "%d.%m.%Y"


def money_equal(a: float, b: float) -> bool:
    return abs(a - b) <= MONEY_TOLERANCE


def check_jib(field: str, party: Party) -> list[str]:
    jib = party.jib
    if not jib.isdigit():
        return [f"{field}: expected digits only, got '{jib}'"]
    if len(jib) != JIB_LENGTH:
        return [f"{field}: expected {JIB_LENGTH} digits, got {len(jib)} ('{jib}')"]
    return []


def check_items(invoice: Invoice) -> list[str]:
    errors = []
    for i, item in enumerate(invoice.items):
        expected = item.quantity * item.unit_price
        if not money_equal(expected, item.amount):
            errors.append(
                f"items[{i}].amount ('{item.description}'): "
                f"expected {expected:.2f} ({item.quantity} x {item.unit_price:.2f}), got {item.amount:.2f}"
            )
    return errors


def check_totals(invoice: Invoice) -> list[str]:
    errors = []

    items_sum = sum(item.amount for item in invoice.items)
    if not money_equal(items_sum, invoice.subtotal):
        errors.append(
            f"subtotal: expected {items_sum:.2f} (sum of items), got {invoice.subtotal:.2f}"
        )

    expected_vat = invoice.subtotal * VAT_RATE
    if not money_equal(expected_vat, invoice.vat):
        errors.append(
            f"vat: expected {expected_vat:.2f} (17% of subtotal), got {invoice.vat:.2f}"
        )

    expected_total = invoice.subtotal + invoice.vat
    if not money_equal(expected_total, invoice.total):
        errors.append(
            f"total: expected {expected_total:.2f} (subtotal + vat), got {invoice.total:.2f}"
        )

    return errors


def check_date(invoice: Invoice) -> list[str]:
    try:
        invoice_date = datetime.strptime(invoice.date, DATE_FORMAT).date()
    except ValueError:
        return [
            f"date: expected a valid date in DD.MM.YYYY format, got '{invoice.date}'"
        ]

    if invoice_date > date.today():
        return [f"date: expected a date not in the future, got '{invoice.date}'"]
    return []


def validate_invoice(invoice: Invoice) -> list[str]:
    return [
        *check_jib("seller.jib", invoice.seller),
        *check_jib("buyer.jib", invoice.buyer),
        *check_items(invoice),
        *check_totals(invoice),
        *check_date(invoice),
    ]


if __name__ == "__main__":
    from dotenv import load_dotenv

    from extract import extract_invoice

    load_dotenv()

    invoice, _ = extract_invoice("invoices/invoice1.png")
    errors = validate_invoice(invoice)

    if errors:
        print(f"INVALID: {len(errors)} problem(s) found")
        for error in errors:
            print("  -", error)
    else:
        print("VALID: all checks passed")
