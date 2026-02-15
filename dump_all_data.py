import sqlite3

def dump_data():
    conn = sqlite3.connect('pos.db')
    cursor = conn.cursor()
    
    print("--- PRODUCTS ---")
    cursor.execute("SELECT * FROM product")
    products = cursor.fetchall()
    for p in products:
        print(p)
        
    print("\n--- SALES ---")
    cursor.execute("SELECT * FROM sale")
    sales = cursor.fetchall()
    for s in sales:
        print(s)
        
    conn.close()

if __name__ == "__main__":
    dump_data()
