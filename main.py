from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlmodel import SQLModel, Session, create_engine, select
from models import Product, Sale  # ดึงโครงสร้างมาจากไฟล์ models.py
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

# เมื่อโปรแกรมเริ่มทำงาน ให้สร้าง Database ทันที
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

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
