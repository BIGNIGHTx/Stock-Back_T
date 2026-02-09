from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel

class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    sku: str
    category: str
    price: float
    stock: int
    image: Optional[str] = None

class Sale(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int
    product_name: str
    quantity: int
    total_price: float
    created_at: datetime = Field(default_factory=datetime.now)
