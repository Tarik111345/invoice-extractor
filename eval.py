import json
import time
from pathlib import Path

from dotenv import load_dotenv

from extract import extract_invoice
from schema import Invoice
from validation import validate_invoice

EVAL_DIR = Path("invoices/eval")
ANSWERS_FILE = EVAL_DIR / "answers.json"
RESULTS_FILE = EVAL_DIR / "results.json"
MONEY_TOLERANCE = 0.01
SECONDS_BETWEEN_CALLS = 5
MAX_ATTEMPTS = 3

FIELDS = [
    "invoice_number",
    "date",
    "seller.name",
    "seller.jib",
    "buyer.name",
    "buyer.jib",
    "items",
    "subtotal",
    "vat",
    "total",
    "currency",
]


def get_field(invoice: Invoice, field: str):
    value = invoice
    for part in field.split("."):
        value = getattr(value, part)
    return value


def values_equal(expected, actual) -> bool:
    if isinstance(expected, float):
        return abs(expected - actual) <= MONEY_TOLERANCE
    if isinstance(expected, str):
        return expected.strip() == actual.strip()
    if isinstance(expected, list):
        return len(expected) == len(actual) and all(
            values_equal(e.description, a.description)
            and values_equal(e.quantity, a.quantity)
            and values_equal(e.unit_price, a.unit_price)
            and values_equal(e.amount, a.amount)
            for e, a in zip(expected, actual)
        )
    return expected == actual


def compare(expected: Invoice, actual: Invoice) -> dict[str, bool]:
    return {
        field: values_equal(get_field(expected, field), get_field(actual, field))
        for field in FIELDS
    }


def extract_with_retry(image_path: Path) -> Invoice:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            invoice, _ = extract_invoice(str(image_path))
            return invoice
        except Exception as error:
            if attempt == MAX_ATTEMPTS:
                raise
            print(
                f"    attempt {attempt} failed ({error.__class__.__name__}), retrying..."
            )
            time.sleep(SECONDS_BETWEEN_CALLS * attempt * 2)


def run_eval() -> list[dict]:
    answers = json.loads(ANSWERS_FILE.read_text(encoding="utf-8"))
    results = []

    for filename, answer in answers.items():
        expected = Invoice(**answer)
        print(f"  {filename} ...")
        try:
            actual = extract_with_retry(EVAL_DIR / filename)
        except Exception as error:
            print(f"    FAILED: {error.__class__.__name__}")
            results.append({"file": filename, "failed": True})
            continue

        results.append(
            {
                "file": filename,
                "failed": False,
                "fields": compare(expected, actual),
                "validation_errors": validate_invoice(actual),
                "expected": expected.model_dump(),
                "actual": actual.model_dump(),
            }
        )
        time.sleep(SECONDS_BETWEEN_CALLS)

    return results


def print_report(results: list[dict]) -> None:
    done = [r for r in results if not r["failed"]]
    failed = len(results) - len(done)
    if not done:
        print("No invoices were processed.")
        return

    print(f"\nACCURACY PER FIELD ({len(done)} invoices, {failed} failed API calls)")
    for field in FIELDS:
        correct = sum(r["fields"][field] for r in done)
        percent = correct / len(done) * 100
        bar = "#" * round(percent / 5)
        print(f"  {field:<15} {percent:5.1f}%  {bar:<20} {correct}/{len(done)}")

    fully_correct = [r for r in done if all(r["fields"].values())]
    with_mistakes = [r for r in done if not all(r["fields"].values())]
    caught = [r for r in with_mistakes if r["validation_errors"]]
    silent = [r for r in with_mistakes if not r["validation_errors"]]
    false_alarms = [r for r in fully_correct if r["validation_errors"]]

    print("\nINVOICES")
    print(f"  fully correct:            {len(fully_correct)}/{len(done)}")
    print(f"  with mistakes:            {len(with_mistakes)}/{len(done)}")
    print(f"    caught by validation:   {len(caught)}")
    print(f"    SILENT (not caught):    {len(silent)}")
    print(f"  false alarms:             {len(false_alarms)}")

    for r in silent:
        wrong = [field for field, ok in r["fields"].items() if not ok]
        print(f"  ! silent mistake in {r['file']}: {', '.join(wrong)}")


if __name__ == "__main__":
    load_dotenv()

    print("Running eval...")
    results = run_eval()
    RESULTS_FILE.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print_report(results)
    print(f"\nDetailed results saved to {RESULTS_FILE}")
