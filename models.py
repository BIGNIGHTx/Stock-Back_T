from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel

class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    sku: str
    category: str
    price: float
    cost_price: float  # ราคาต้นทุน
    stock: int
    has_vat: bool = Field(default=False)
    image: Optional[str] = None

class Sale(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int
    product_name: str
    quantity: int
    total_price: float
    created_at: datetime = Field(default_factory=datetime.now)

class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str                          # ชื่อภาษาอังกฤษ (ใช้เป็น key)
    name_th: Optional[str] = None      # ชื่อภาษาไทย
    image: Optional[str] = None        # URL รูปภาพ

class Brand(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str                          # ชื่อแบรนด์
