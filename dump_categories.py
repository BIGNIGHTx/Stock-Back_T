import sqlite3

def dump_categories():
    conn = sqlite3.connect('pos.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM category")
    rows = cursor.fetchall()
    print("Categories in DB:")
    for row in rows:
        print(row)
    conn.close()

if __name__ == "__main__":
    dump_categories()
