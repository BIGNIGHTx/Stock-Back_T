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

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

app = FastAPI()

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_detail = {
        "error": str(exc),
        "type": type(exc).__name__,
        "traceback": traceback.format_exc()
    }
    print(f"❌ Error occurred: {error_detail}")
    return JSONResponse(status_code=500, content=error_detail)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CategoryCreate(BaseModel):
    name: str
    thai: Optional[str] = None
    image: Optional[str] = None

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    thai: Optional[str] = None
    image: Optional[str] = None

class BrandCreate(BaseModel):
    name: str

DEFAULT_CATEGORIES = [
    {"name": "Tv",              "thai": "โทรทัศน์",       "image": "https://images.unsplash.com/photo-1717295248230-93ea71f48f92?w=600&auto=format&fit=crop&q=60"},
    {"name": "Fan",             "thai": "พัดลม",           "image": "https://media.istockphoto.com/id/1150705585/th/รูปถ่าย/ภาพระยะใกล้ของพัดลมตั้งพื้นไฟฟ้า.jpg?s=612x612&w=0&k=20&c=vX1hV1muUVa96MZpx4jJd6Ujl54pQX6Z8eIyyrdkLvw="},
    {"name": "Refrigerator",    "thai": "ตู้เย็น",          "image": "https://images.unsplash.com/photo-1584568694244-14fbdf83bd30?w=600&auto=format&fit=crop&q=60"},
    {"name": "Washing Machine", "thai": "เครื่องซักผ้า",   "image": "https://images.unsplash.com/photo-1626806787461-102c1bfaaea1?w=600&auto=format&fit=crop&q=60"},
]

DEFAULT_BRANDS = [
    {"name": "Samsung"},
    {"name": "LG"},
    {"name": "Mitsubishi"},
    {"name": "Sharp"},
    {"name": "Hitachi"},
    {"name": "Panasonic"},
]

@app.on_event("startup")
def on_startup():
    # --- Auto-Migration: rename name_th → thai ---
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

    create_db_and_tables()

    with Session(engine) as session:
        existing_cats = session.exec(select(Category)).all()
        # ✅ เช็คด้วย lowercase เพื่อกัน duplicate เช่น "TV" vs "Tv"
        existing_names_lower = {c.name.lower(): c for c in existing_cats}
        existing_names_exact = {c.name: c for c in existing_cats}

        # 1. Seed DEFAULT_CATEGORIES
        for d_cat in DEFAULT_CATEGORIES:
            name = d_cat["name"]
            name_lower = name.lower()
            if name_lower in existing_names_lower:
                # ถ้ามีชื่อซ้ำ (case-insensitive) → อัปเดตรูปและชื่อให้ตรง
                cat_obj = existing_names_lower[name_lower]
                cat_obj.image = d_cat["image"]
                if cat_obj.name != name:
                    # ✅ แก้ชื่อใน product ด้วยถ้าไม่ตรง
                    old_name = cat_obj.name
                    products_to_fix = session.exec(
                        select(Product).where(Product.category == old_name)
                    ).all()
                    for p in products_to_fix:
                        p.category = name
                        session.add(p)
                    cat_obj.name = name
                session.add(cat_obj)
            else:
                session.add(Category(**d_cat))

        session.commit()

        # Refresh หลัง commit
        existing_cats = session.exec(select(Category)).all()
        existing_names_lower = {c.name.lower(): c for c in existing_cats}

        # 2. ✅ Sync product categories — เช็ค case-insensitive ก่อนเพิ่ม
        product_cats = session.exec(select(Product.category).distinct()).all()
        default_names_lower = [d["name"].lower() for d in DEFAULT_CATEGORIES]

        for p_cat in product_cats:
            if not p_cat:
                continue
            p_cat_lower = p_cat.lower()
            # ถ้ามีใน DB แล้ว (ไม่ว่าจะ case ไหน) → ไม่เพิ่ม
            if p_cat_lower in existing_names_lower:
                continue
            # ถ้าไม่มีเลย → เพิ่มใหม่
            session.add(Category(name=p_cat, thai=p_cat))

        session.commit()


# --- PRODUCTS ---

@app.post("/products/")
def create_product(product: Product):
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

@app.get("/products/")
def read_products():
    with Session(engine) as session:
        return session.exec(select(Product)).all()

@app.put("/products/{product_id}")
def update_product(product_id: int, product_data: Product):
    with Session(engine) as session:
        db_product = session.get(Product, product_id)
        if not db_product:
            raise HTTPException(status_code=404, detail="Product not found")
        product_data_dict = product_data.model_dump(exclude_unset=True)
        for key, value in product_data_dict.items():
            setattr(db_product, key, value)
        session.add(db_product)
        session.commit()
        session.refresh(db_product)
        return db_product

@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    with Session(engine) as session:
        product = session.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        session.delete(product)
        session.commit()
        return {"ok": True}

# --- SALES ---

@app.post("/sales/")
def create_sale(sale: Sale):
    with Session(engine) as session:
        product = session.get(Product, sale.product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        if product.stock < sale.quantity:
            raise HTTPException(status_code=400, detail="Not enough stock")
        product.stock -= sale.quantity
        session.add(product)
        sale.created_at = datetime.now()
        session.add(sale)
        session.commit()
        session.refresh(sale)
        return sale

@app.get("/sales/")
def read_sales():
    with Session(engine) as session:
        return session.exec(select(Sale)).all()

@app.delete("/sales/{sale_id}")
def delete_sale(sale_id: int):
    with Session(engine) as session:
        sale = session.get(Sale, sale_id)
        if not sale:
            raise HTTPException(status_code=404, detail="Sale not found")
        product = session.get(Product, sale.product_id)
        if product:
            product.stock += sale.quantity
            session.add(product)
        session.delete(sale)
        session.commit()
        return {"ok": True}

# --- CATEGORIES ---

@app.get("/categories/")
def read_categories():
    with Session(engine) as session:
        return session.exec(select(Category)).all()

# --- DASHBOARD ---
@app.get("/dashboard/inventory_by_category")
def inventory_by_category():
    with Session(engine) as session:
        # ดึงหมวดหมู่ทั้งหมด
        categories = session.exec(select(Category)).all()
        # ดึงสินค้าทั้งหมด
        products = session.exec(select(Product)).all()
        # สรุปจำนวนสินค้าคงเหลือแยกตามหมวดหมู่
        result = []
        for cat in categories:
            cat_products = [p for p in products if p.category == cat.name]
            total_stock = sum(p.stock for p in cat_products if p.stock is not None)
            result.append({
                "category_id": cat.id,
                "category_name": cat.name,
                "thai": cat.thai,
                "image": cat.image,
                "total_stock": total_stock,
                "product_count": len(cat_products),
                "products": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "stock": p.stock,
                        "price": p.price,
                        "cost_price": p.cost_price,
                        "has_vat": p.has_vat,
                        "image": p.image
                    } for p in cat_products
                ]
            })
        return result

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
        # ✅ อัปเดตชื่อ category ในสินค้าทุกตัวอัตโนมัติ
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

# --- BRANDS ---

@app.get("/brands/")
def read_brands():
    with Session(engine) as session:
        return session.exec(select(Brand)).all()

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
