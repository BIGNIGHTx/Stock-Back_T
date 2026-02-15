import sqlite3

def dump_to_file():
    conn = sqlite3.connect('pos.db')
    cursor = conn.cursor()
    
    with open('db_dump.txt', 'w', encoding='utf-8') as f:
        f.write("--- PRODUCTS ---\n")
        cursor.execute("SELECT * FROM product")
        products = cursor.fetchall()
        for p in products:
            f.write(str(p) + "\n")
            
        f.write("\n--- SALES ---\n")
        cursor.execute("SELECT * FROM sale")
        sales = cursor.fetchall()
        for s in sales:
            f.write(str(s) + "\n")
            
    conn.close()

if __name__ == "__main__":
    dump_to_file()
