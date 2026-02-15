import sqlite3

def cleanup_garbage():
    conn = sqlite3.connect('pos.db')
    cursor = conn.cursor()
    
    # 1. Identify products to delete (Price < 100)
    cursor.execute("SELECT id, name, price FROM product WHERE price < 100")
    garbage_products = cursor.fetchall()
    
    if not garbage_products:
        print("No garbage products found (Price < 100).")
        conn.close()
        return

    print("Found garbage products:")
    garbage_ids = []
    for p in garbage_products:
        print(f"- ID: {p[0]}, Name: {p[1]}, Price: {p[2]}")
        garbage_ids.append(p[0])
        
    ids_tuple = tuple(garbage_ids)
    if len(ids_tuple) == 1:
        ids_tuple = f"({ids_tuple[0]})"
    else:
        ids_tuple = str(ids_tuple)

    # 2. Delete sales referencing these products
    print(f"\nDeleting sales for product IDs: {ids_tuple}")
    cursor.execute(f"DELETE FROM sale WHERE product_id IN {ids_tuple}")
    sales_deleted = cursor.rowcount
    print(f"Deleted {sales_deleted} sales records.")
    
    # 3. Delete the products
    print(f"Deleting products with IDs: {ids_tuple}")
    cursor.execute(f"DELETE FROM product WHERE id IN {ids_tuple}")
    products_deleted = cursor.rowcount
    print(f"Deleted {products_deleted} product records.")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    cleanup_garbage()
