import sqlite3

def add_vat_column():
    conn = sqlite3.connect('pos.db')
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE product ADD COLUMN has_vat BOOLEAN DEFAULT 0")
        conn.commit()
        print("Successfully added has_vat column to product table.")
    except sqlite3.OperationalError as e:
        print(f"Error: {e}")
        # Possibly column already exists
    finally:
        conn.close()

if __name__ == "__main__":
    add_vat_column()
