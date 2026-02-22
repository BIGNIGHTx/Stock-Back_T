from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlmodel import SQLModel, Session, create_engine, select
from pydantic import BaseModel
from models import Product, Sale, Category, Brand  # ดึงโครงสร้างมาจากไฟล์ models.py
from fastapi.middleware.cors import CORSMiddleware
import traceback

# 1. ตั้งค่า Database (SQLite)
sqlite_file_name = "pos.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# check_same_thread=False จำเป็นสำหรับ SQLite ใน FastAPI
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

# ฟังก์ชันสร้างตารางใน Database
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# 2. สร้าง App และตั้งค่า Event
app = FastAPI()

# เพิ่ม Exception Handler เพื่อ debug
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_detail = {
        "error": str(exc),
        "type": type(exc).__name__,
        "traceback": traceback.format_exc()
    }
    print(f"❌ Error occurred: {error_detail}")  # พิมพ์ใน console
    return JSONResponse(
        status_code=500,
        content=error_detail
    )

# เปิดให้ React เข้าถึงได้
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Schemas สำหรับ Category และ Brand ---
class CategoryCreate(BaseModel):
    name: str
    name_th: Optional[str] = None
    image: Optional[str] = None

class BrandCreate(BaseModel):
    name: str

# ข้อมูล Category และ Brand เริ่มต้น
DEFAULT_CATEGORIES = [
    {"name": "Beverage",   "name_th": "เครื่องดื่ม",  "image": None},
    {"name": "Snack",      "name_th": "ขนม",            "image": None},
    {"name": "Dairy",      "name_th": "นม/โยเกิร์ต",   "image": None},
    {"name": "Cleaning",   "name_th": "ของใช้ทำความสะอาด", "image": None},
    {"name": "Noodle",     "name_th": "บะหมี่กึ่งสำเร็จรูป", "image": None},
]

DEFAULT_BRANDS = [
    {"name": "Lay's"},
    {"name": "Nestle"},
    {"name": "Unilever"},
    {"name": "Mama"},
]

# เมื่อโปรแกรมเริ่มทำงาน ให้สร้าง Database ทันที
@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    # Seed ข้อมูลเริ่มต้นถ้ายังไม่มี
    with Session(engine) as session:
        # Seed Categories
        existing_cats = session.exec(select(Category)).all()
        if not existing_cats:
            for cat in DEFAULT_CATEGORIES:
                session.add(Category(**cat))
        # Seed Brands
        existing_brands = session.exec(select(Brand)).all()
        if not existing_brands:
            for brand in DEFAULT_BRANDS:
                session.add(Brand(**brand))
        session.commit()

# --- API ENDPOINTS (จุดรับ-ส่งข้อมูล) ---

# 3. เพิ่มสินค้าใหม่ (Create)
@app.post("/products/")
def create_product(product: Product):
    # Validate required fields
    if product.cost_price is None:
        raise HTTPException(status_code=422, detail="cost_price is required")
    if product.price is None:
        raise HTTPException(status_code=422, detail="price is required")
    if product.stock is None:
        raise HTTPException(status_code=422, detail="stock is required")
    
    with Session(engine) as session:
        session.add(product)
        session.commit()
        session.refresh(product)
        return product

# 4. ดึงข้อมูลสินค้าทั้งหมด (Read)
@app.get("/products/")
def read_products():
    with Session(engine) as session:
        products = session.exec(select(Product)).all()
        return products

# 5. อัปเดตสินค้า (Update - ตัดสต๊อก/แก้ไข)
@app.put("/products/{product_id}")
def update_product(product_id: int, product_data: Product):
    with Session(engine) as session:
        db_product = session.get(Product, product_id)
        if not db_product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # อัปเดตข้อมูล
        product_data_dict = product_data.model_dump(exclude_unset=True)
        for key, value in product_data_dict.items():
            setattr(db_product, key, value)
            
        session.add(db_product)
        session.commit()
        session.refresh(db_product)
        return db_product

# 6. ลบสินค้า (Delete)
@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    with Session(engine) as session:
        product = session.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        session.delete(product)
        session.commit()
        return {"ok": True}

# --- API สำหรับการขาย ---
@app.post("/sales/")
def create_sale(sale: Sale):
    with Session(engine) as session:
        # 1. ค้นหาสินค้าที่จะขาย
        product = session.get(Product, sale.product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # 2. เช็คสต๊อกว่าพอไหม
        if product.stock < sale.quantity:
            raise HTTPException(status_code=400, detail="Not enough stock")
        
        # 3. ตัดสต๊อก
        product.stock -= sale.quantity
        session.add(product) # อัปเดตสินค้า
        
        # 4. บันทึกประวัติการขาย
        sale.created_at = datetime.now() # ใส่วันที่ปัจจุบัน
        session.add(sale) # สร้างบิลขาย
        
        session.commit()
        session.refresh(sale)
        return sale

@app.get("/sales/")
def read_sales():
    with Session(engine) as session:
        sales = session.exec(select(Sale)).all()
        return sales

# 7. ลบข้อมูลการขาย (Delete Sale)
@app.delete("/sales/{sale_id}")
def delete_sale(sale_id: int):
    with Session(engine) as session:
        sale = session.get(Sale, sale_id)
        if not sale:
            raise HTTPException(status_code=404, detail="Sale not found")
        
        # คืนสต๊อกสินค้า
        product = session.get(Product, sale.product_id)
        if product:
             product.stock += sale.quantity
             session.add(product)
        
        session.delete(sale)
        session.commit()
        return {"ok": True}

# --- API สำหรับ Category ---

@app.get("/categories/")
def read_categories():
    with Session(engine) as session:
        categories = session.exec(select(Category)).all()
        return categories

@app.post("/categories/")
def create_category(data: CategoryCreate):
    with Session(engine) as session:
        # ตรวจสอบว่าชื่อซ้ำไหม
        existing = session.exec(
            select(Category).where(Category.name == data.name)
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Category '{data.name}' already exists")
        cat = Category(name=data.name, name_th=data.name_th, image=data.image)
        session.add(cat)
        session.commit()
        session.refresh(cat)
        return cat

@app.delete("/categories/{category_id}")
def delete_category(category_id: int):
    with Session(engine) as session:
        cat = session.get(Category, category_id)
        if not cat:
            raise HTTPException(status_code=404, detail="Category not found")
        session.delete(cat)
        session.commit()
        return {"ok": True, "deleted_id": category_id}

# --- API สำหรับ Brand ---

@app.get("/brands/")
def read_brands():
    with Session(engine) as session:
        brands = session.exec(select(Brand)).all()
        return brands

@app.post("/brands/")
def create_brand(data: BrandCreate):
    with Session(engine) as session:
        existing = session.exec(
            select(Brand).where(Brand.name == data.name)
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Brand '{data.name}' already exists")
        brand = Brand(name=data.name)
        session.add(brand)
        session.commit()
        session.refresh(brand)
        return brand

@app.delete("/brands/{brand_id}")
def delete_brand(brand_id: int):
    with Session(engine) as session:
        brand = session.get(Brand, brand_id)
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        session.delete(brand)
        session.commit()
        return {"ok": True, "deleted_id": brand_id}
