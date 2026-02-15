import sqlite3

def list_products():
    conn = sqlite3.connect('pos.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, sku, has_vat FROM product")
    products = cursor.fetchall()
    conn.close()
    
    print(f"{'ID':<5} {'Name':<30} {'SKU':<15} {'Has VAT'}")
    print("-" * 60)
    for p in products:
        has_vat = p[3] if len(p) > 3 else 0
        print(f"{p[0]:<5} {p[1]:<30} {p[2]:<15} {has_vat}")

if __name__ == "__main__":
    list_products()
