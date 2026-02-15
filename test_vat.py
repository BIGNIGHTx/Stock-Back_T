import requests

BASE_URL = "http://127.0.0.1:8000"

def test_vat_functionality():
    # 1. Create a product with has_vat=True
    product_data = {
        "name": "Test Product VAT",
        "sku": "TEST-VAT-001",
        "category": "Test",
        "price": 100.0,
        "cost_price": 50.0,
        "stock": 10,
        "has_vat": True
    }
    
    print("Creating product with has_vat=True...")
    response = requests.post(f"{BASE_URL}/products/", json=product_data)
    if response.status_code != 200:
        print(f"Failed to create product: {response.text}")
        return

    product = response.json()
    product_id = product["id"]
    print(f"Created product: {product}")
    
    if product.get("has_vat") is True:
        print("✅ Success: Product created with has_vat=True")
    else:
        print("❌ Failure: Product created but has_vat is not True")

    # 2. Update product to has_vat=False
    print("\nUpdating product to has_vat=False...")
    update_data = {
        "name": "Test Product VAT Updated",
        "sku": "TEST-VAT-001",
        "category": "Test",
        "price": 100.0,
        "cost_price": 50.0,
        "stock": 10,
        "has_vat": False
    }
    response = requests.put(f"{BASE_URL}/products/{product_id}", json=update_data)
    if response.status_code != 200:
        print(f"Failed to update product: {response.text}")
        return

    updated_product = response.json()
    print(f"Updated product: {updated_product}")

    if updated_product.get("has_vat") is False:
        print("✅ Success: Product updated to has_vat=False")
    else:
        print("❌ Failure: Product updated but has_vat is not False")

    # Clean up
    requests.delete(f"{BASE_URL}/products/{product_id}")
    print("\nCleaned up test product.")

if __name__ == "__main__":
    test_vat_functionality()
