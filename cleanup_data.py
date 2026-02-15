import sqlite3

def delete_test_data():
    conn = sqlite3.connect('pos.db')
    cursor = conn.cursor()
    
    # Deleting the specific TEST999 item seen in output
    cursor.execute("DELETE FROM product WHERE sku = 'TEST999'")
    
    # Also delete any other obvious test data if any
    cursor.execute("DELETE FROM product WHERE name LIKE 'Test%' OR sku LIKE 'TEST%'")
    
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    
    print(f"Deleted {deleted_count} test items.")

if __name__ == "__main__":
    delete_test_data()
