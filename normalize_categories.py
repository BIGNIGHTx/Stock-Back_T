import sqlite3

def normalize_db():
    conn = sqlite3.connect('pos.db')
    cursor = conn.cursor()
    
    # 1. Get unique categories from products
    cursor.execute("SELECT DISTINCT category FROM product")
    product_cats = [row[0] for row in cursor.fetchall() if row[0]]
    
    # 2. Get existing categories from category table
    cursor.execute("SELECT id, name FROM category")
    existing_cats = {row[1]: row[0] for row in cursor.fetchall()}
    
    # 3. Add missing categories to category table
    defaults = {
        "Tv": "โทรทัศน์",
        "Fan": "พัดลม",
        "Refrigerator": "ตู้เย็น",
        "Washing Machine": "เครื่องซักผ้า"
    }
    
    for cat_name in product_cats:
        if cat_name not in existing_cats:
            thai = defaults.get(cat_name, "")
            cursor.execute("INSERT INTO category (name, thai) VALUES (?, ?)", (cat_name, thai))
            print(f"Added missing category: {cat_name}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    normalize_db()
