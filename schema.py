from pydantic import BaseModel


class Party(BaseModel):
    name: str
    jib: str


class LineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    amount: float


class Invoice(BaseModel):
    invoice_number: str
    date: str
    seller: Party
    buyer: Party
    items: list[LineItem]
    subtotal: float
    vat: float
    total: float
    currency: str
