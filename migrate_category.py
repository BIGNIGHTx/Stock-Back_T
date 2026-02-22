"""
Migration: ปรับ category table ให้ตรงกับ model ใหม่
- เปลี่ยน column name_th → thai
- สร้างตาราง category และ brand ถ้ายังไม่มี
"""
import sqlite3

DB_PATH = "pos.db"

def run():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # ตรวจสอบ columns ที่มีใน category table
    cur.execute("PRAGMA table_info(category)")
    cols = [row[1] for row in cur.fetchall()]
    print(f"Category columns: {cols}")

    if "category" not in [t[0] for t in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]:
        print("ไม่มีตาราง category — จะสร้างใหม่ผ่าน SQLModel")
    elif "name_th" in cols and "thai" not in cols:
        print("🔄 Renaming name_th → thai ...")
        # SQLite ไม่รองรับ RENAME COLUMN โดยตรงใน version เก่า ต้องทำผ่าน recreate
        cur.execute("""
            CREATE TABLE category_new (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                thai TEXT,
                image TEXT
            )
        """)
        cur.execute("INSERT INTO category_new (id, name, thai, image) SELECT id, name, name_th, image FROM category")
        cur.execute("DROP TABLE category")
        cur.execute("ALTER TABLE category_new RENAME TO category")
        con.commit()
        print("✅ เปลี่ยน name_th → thai เรียบร้อย")
    elif "thai" in cols:
        print("✅ Column 'thai' มีอยู่แล้ว ไม่ต้อง migrate")
    else:
        print(f"⚠️  Column ที่เจอ: {cols} — ไม่แน่ใจ ข้ามไป")

    # ตรวจสอบ brand table
    tables = [t[0] for t in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    if "brand" not in tables:
        print("🔄 สร้างตาราง brand ...")
        cur.execute("""
            CREATE TABLE brand (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        """)
        con.commit()
        print("✅ สร้างตาราง brand เรียบร้อย")
    else:
        print("✅ ตาราง brand มีอยู่แล้ว")

    con.close()
    print("\n🎉 Migration เสร็จสมบูรณ์")

if __name__ == "__main__":
    run()
