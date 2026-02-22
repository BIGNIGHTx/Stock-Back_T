from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlmodel import SQLModel, Session, create_engine, select
from pydantic import BaseModel
from models import Product, Sale, Category, Brand
from fastapi.middleware.cors import CORSMiddleware
import traceback
import sqlite3

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
    thai: Optional[str] = None     # ชื่อภาษาไทย ตรงกับ frontend
    image: Optional[str] = None

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    thai: Optional[str] = None
    image: Optional[str] = None

class BrandCreate(BaseModel):
    name: str

# ข้อมูล Category และ Brand เริ่มต้น
DEFAULT_CATEGORIES = [
    {"name": "Tv",          "thai": "โทรทัศน์",          "image": "https://images.unsplash.com/photo-1717295248230-93ea71f48f92?w=600&auto=format&fit=crop&q=60"},
    {"name": "Fan",         "thai": "พัดลม",              "image": "https://media.istockphoto.com/id/1150705585/th/รูปถ่าย/ภาพระยะใกล้ของพัดลมตั้งพื้นไฟฟ้า.jpg?s=612x612&w=0&k=20&c=vX1hV1muUVa96MZpx4jJd6Ujl54pQX6Z8eIyyrdkLvw="},
    {"name": "Refrigerator","thai": "ตู้เย็น",             "image": "https://images.unsplash.com/photo-1584568694244-14fbdf83bd30?w=600&auto=format&fit=crop&q=60"},
    {"name": "Washing Machine", "thai": "เครื่องซักผ้า",  "image": "https://images.unsplash.com/photo-1626806787461-102c1bfaaea1?w=600&auto=format&fit=crop&q=60"},
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
    # --- Auto-Migration: rename name_th → thai ถ้ายังเป็น column เก่า ---
    try:
        con = sqlite3.connect(sqlite_file_name)
        cur = con.cursor()
        tables = [t[0] for t in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        if "category" in tables:
            cols = [row[1] for row in cur.execute("PRAGMA table_info(category)").fetchall()]
            if "name_th" in cols and "thai" not in cols:
                print("🔄 Migrating: rename name_th → thai in category table...")
                cur.execute("""
                    CREATE TABLE category_new (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        thai TEXT,
                        image TEXT
                    )
                """)
                cur.execute("INSERT INTO category_new (id, name, thai, image) SELECT id, name, name_th, image FROM category")
                cur.execute("DROP TABLE category")
                cur.execute("ALTER TABLE category_new RENAME TO category")
                con.commit()
                print("✅ Migration เสร็จแล้ว: name_th → thai")
        con.close()
    except Exception as e:
        print(f"⚠️ Migration error (ข้ามได้): {e}")

    # สร้าง/อัปเดต tables ตาม model
    create_db_and_tables()

    # --- Sync categories from Products to Category table ---
    with Session(engine) as session:
        # 1. Get unique categories currently used in products
        product_cats = session.exec(select(Product.category).distinct()).all()
        
        # 2. Get existing categories in the Category table
        existing_cats = session.exec(select(Category)).all()
        existing_names = {c.name: c for c in existing_cats}
        
        # 3. Ensure DEFAULT_CATEGORIES exist and have images
        for d_cat in DEFAULT_CATEGORIES:
            name = d_cat["name"]
            if name in existing_names:
                # Update image if it's missing or different (optional, but good for restoring defaults)
                cat_obj = existing_names[name]
                if not cat_obj.image or cat_obj.image != d_cat["image"]:
                    cat_obj.image = d_cat["image"]
                    session.add(cat_obj)
            else:
                session.add(Category(**d_cat))
        
        # 4. Add any other categories found in products that aren't in the table
        for p_cat in product_cats:
            if p_cat and p_cat not in existing_names and p_cat not in [d["name"] for d in DEFAULT_CATEGORIES]:
                 session.add(Category(name=p_cat, thai=p_cat))
                 
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
        existing = session.exec(
            select(Category).where(Category.name == data.name)
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Category '{data.name}' already exists")
        cat = Category(name=data.name, thai=data.thai, image=data.image)
        session.add(cat)
        session.commit()
        session.refresh(cat)
        return cat

@app.put("/categories/{category_id}")
def update_category(category_id: int, data: CategoryUpdate):
    with Session(engine) as session:
        db_cat = session.get(Category, category_id)
        if not db_cat:
            raise HTTPException(status_code=404, detail="Category not found")
        
        old_name = db_cat.name
        update_data = data.model_dump(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(db_cat, key, value)
            
        new_name = db_cat.name
        
        # ถ้านามชื่อเปลี่ยน ให้ไปอัปเดตสินค้าทุกตัวที่ใช้ชื่อเดิม
        if old_name != new_name:
            products_to_update = session.exec(
                select(Product).where(Product.category == old_name)
            ).all()
            for p in products_to_update:
                p.category = new_name
                session.add(p)
                
        session.add(db_cat)
        session.commit()
        session.refresh(db_cat)
        return db_cat

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
