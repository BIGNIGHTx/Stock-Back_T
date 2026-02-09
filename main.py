from fastapi import FastAPI, HTTPException
from sqlmodel import SQLModel, Session, create_engine, select
from models import Product  # ดึงโครงสร้างมาจากไฟล์ models.py
from fastapi.middleware.cors import CORSMiddleware

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

# เปิดให้ React เข้าถึงได้
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# เมื่อโปรแกรมเริ่มทำงาน ให้สร้าง Database ทันที
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# --- API ENDPOINTS (จุดรับ-ส่งข้อมูล) ---

# 3. เพิ่มสินค้าใหม่ (Create)
@app.post("/products/")
def create_product(product: Product):
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
        product_data_dict = product_data.dict(exclude_unset=True)
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
