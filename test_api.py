"""
ไฟล์ทดสอบ API เพื่อหาสาเหตุข้อผิดพลาด
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_create_product_success():
    """ทดสอบกรณีส่งข้อมูลครบถ้วน - ต้องสำเร็จ"""
    print("\n=== ทดสอบ 1: ส่งข้อมูลครบถ้วน ===")
    data = {
        "name": "ทดสอบสินค้า",
        "sku": "TEST001", 
        "category": "อาหาร",
        "price": 100.0,
        "cost_price": 50.0,
        "stock": 10
    }
    try:
        r = requests.post(f"{BASE_URL}/products/", json=data)
        print(f"✅ Status: {r.status_code}")
        print(f"Response: {r.json()}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_create_product_with_image():
    """ทดสอบกรณีมีรูปภาพ - ต้องสำเร็จ"""
    print("\n=== ทดสอบ 2: ส่งข้อมูลพร้อมรูปภาพ ===")
    data = {
        "name": "สินค้ามีรูป",
        "sku": "TEST002",
        "category": "เครื่องดื่ม", 
        "price": 150.0,
        "cost_price": 75.0,
        "stock": 20,
        "image": "https://example.com/image.jpg"
    }
    try:
        r = requests.post(f"{BASE_URL}/products/", json=data)
        print(f"✅ Status: {r.status_code}")
        print(f"Response: {r.json()}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_create_product_missing_field():
    """ทดสอบกรณีขาดข้อมูล - ต้อง Error"""
    print("\n=== ทดสอบ 3: ส่งข้อมูลไม่ครบ (ขาด cost_price) ===")
    data = {
        "name": "สินค้าไม่ครบ",
        "sku": "TEST003",
        "category": "อื่นๆ",
        "price": 200.0,
        # ขาด cost_price
        "stock": 5
    }
    try:
        r = requests.post(f"{BASE_URL}/products/", json=data)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.json()}")
        if r.status_code != 200:
            print(f"❌ Error ตามที่คาดไว้ - detail: {r.json().get('detail')}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_create_product_wrong_type():
    """ทดสอบกรณีส่งข้อมูลผิดประเภท - ต้อง Error"""
    print("\n=== ทดสอบ 4: ส่งข้อมูลผิดชนิด (price เป็น string) ===")
    data = {
        "name": "สินค้าผิดชนิด",
        "sku": "TEST004",
        "category": "อื่นๆ",
        "price": "ร้อยบาท",  # ผิด! ต้องเป็นตัวเลข
        "cost_price": 50.0,
        "stock": 5
    }
    try:
        r = requests.post(f"{BASE_URL}/products/", json=data)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.json()}")
        if r.status_code != 200:
            print(f"❌ Error ตามที่คาดไว้ - detail: {r.json().get('detail')}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_create_product_negative_stock():
    """ทดสอบกรณีสต๊อกติดลบ"""
    print("\n=== ทดสอบ 5: สต๊อกเป็นจำนวนลบ ===")
    data = {
        "name": "สินค้าสต๊อกลบ",
        "sku": "TEST005",
        "category": "อื่นๆ",
        "price": 100.0,
        "cost_price": 50.0,
        "stock": -5  # สต๊อกติดลบ
    }
    try:
        r = requests.post(f"{BASE_URL}/products/", json=data)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.json()}")
        if r.status_code == 200:
            print(f"⚠️ Warning: ระบบยอมรับสต๊อกติดลบ (อาจต้องเพิ่ม validation)")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 เริ่มทดสอบ API สำหรับบันทึกสินค้า")
    print("=" * 60)
    
    # รันทดสอบทั้งหมด
    test_create_product_success()
    test_create_product_with_image()
    test_create_product_missing_field()
    test_create_product_wrong_type()
    test_create_product_negative_stock()
    
    print("\n" + "=" * 60)
    print("✅ ทดสอบเสร็จสิ้น")
