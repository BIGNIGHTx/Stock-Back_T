import sqlite3

def check_products():
    conn = sqlite3.connect('pos.db')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM product")
    rows = cursor.fetchall()
    print("Unique product categories in DB:")
    for row in rows:
        print(f"'{row[0]}'")
    conn.close()

if __name__ == "__main__":
    check_products()
