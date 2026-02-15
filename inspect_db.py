import sqlite3

def inspect_schema():
    conn = sqlite3.connect('pos.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(product)")
    columns = cursor.fetchall()
    print("Product Table Schema:")
    for col in columns:
        print(col)
    conn.close()

if __name__ == "__main__":
    inspect_schema()
