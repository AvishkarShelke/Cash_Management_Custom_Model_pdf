from fastapi import FastAPI, Body
import re

app = FastAPI()


def to_float(value: str):
    if not value:
        return 0.0
    cleaned = re.sub(r"[^\d.]", "", value)
    return float(cleaned) if cleaned else 0.0


def extract_index(label: str, prefix: str):
    idx = label.replace(prefix, "")
    return idx if idx else "1"


@app.post("/extract")
async def extract_fields(payload: dict = Body(...)):
    customer_name = ""
    payment_reference = None
    total_amount = None

    invoice_numbers = {}
    invoice_amounts = {}

    for page in payload.get("pages", []):
        for field in page.get("documentFields", []):
            raw_label = field.get("fieldLabel", {}).get("name", "")
            label = raw_label.lower()
            value = field.get("fieldValue", {}).get("value", "")

            if label == "customername":
                customer_name = value

            elif label == "paymentreference":
                payment_reference = value

            elif label.startswith("invoicenumber"):
                idx = extract_index(raw_label, "InvoiceNumber")
                invoice_numbers[idx] = f"{value}_{idx}" if not value.isdigit(
                ) else value

            elif label.startswith("amount") and label != "totalamount":
                idx = extract_index(raw_label, "Amount")
                invoice_amounts[idx] = to_float(value)

            elif label == "totalamount":
                total_amount = to_float(value)

    invoices = []

    all_indexes = sorted(
        set(invoice_numbers.keys()) | set(invoice_amounts.keys()),
        key=lambda x: int(x)
    )

    for idx in all_indexes:
        invoices.append({
            "invoiceNumber": invoice_numbers.get(idx),
            "amount": invoice_amounts.get(idx)
        })

    if len(invoices) == 1 and (invoices[0]["amount"] in (None, 0)) and total_amount:
        invoices[0]["amount"] = total_amount

    if total_amount is None:
        total_amount = sum(i["amount"] for i in invoices if i["amount"])

    if not invoices and total_amount:
        invoices.append({
            "invoiceNumber": None,
            "amount": total_amount
        })

    return {
        "customerName": customer_name,
        "paymentReference": payment_reference,
        "invoices": invoices,
        "totalAmount": total_amount
    }
