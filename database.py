import sqlite3
from datetime import datetime


def create_database():
    # Veritabanini ve tablolari olustur
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()

    # Kullanicilar tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id  INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role     TEXT NOT NULL
        )
    """)

    # Urunler tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name   TEXT NOT NULL,
            category       TEXT,
            price          REAL NOT NULL DEFAULT 0,
            stock_quantity INTEGER NOT NULL DEFAULT 0
        )
    """)

    # Satislar tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            sale_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id  INTEGER NOT NULL,
            quantity    INTEGER NOT NULL,
            total_price REAL NOT NULL,
            sale_date   TEXT NOT NULL,
            sold_by     TEXT,
            FOREIGN KEY(product_id) REFERENCES products(product_id)
        )
    """)

    conn.commit()
    conn.close()


def insert_default_users():
    # Varsayilan kullanicilari ekle (admin ve kasiyer)
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
        ("admin", "admin", "admin"),
    )
    cursor.execute(
        "INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
        ("cashier", "cashier", "cashier"),
    )

    conn.commit()
    conn.close()


def check_user(username, password):
    # Kullanici girisini kontrol et
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT role FROM users WHERE username = ? AND password = ?",
        (username, password),
    )
    result = cursor.fetchone()
    conn.close()

    if result:
        return result[0]
    else:
        return None


def add_product(name, category, price, stock):
    # Yeni urun ekle
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO products (product_name, category, price, stock_quantity) VALUES (?, ?, ?, ?)",
        (name, category, price, stock),
    )

    conn.commit()
    conn.close()


def get_products():
    # Tum urunleri getir
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    conn.close()
    return products


def update_product(product_id, name, category, price, stock):
    # Urunu guncelle
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE products SET product_name=?, category=?, price=?, stock_quantity=? WHERE product_id=?",
        (name, category, price, stock, product_id),
    )

    conn.commit()
    conn.close()


def delete_product(product_id):
    # Urunu sil
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM products WHERE product_id = ?", (product_id,))

    conn.commit()
    conn.close()


def get_sales():
    # Tum satislari getir
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM sales")
    sales = cursor.fetchall()

    conn.close()
    return sales


def get_sales_summary():
    # Satis ozetini hesapla: toplam gelir, toplam satis sayisi, en cok satan urun
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()

    # Toplam geliri hesapla
    cursor.execute("SELECT SUM(total_price) FROM sales")
    result = cursor.fetchone()[0]
    if result is None:
        total_revenue = 0
    else:
        total_revenue = result

    # Toplam satis sayisi
    cursor.execute("SELECT COUNT(*) FROM sales")
    total_sales_count = cursor.fetchone()[0]

    # En cok satan urunu bulmak icin tum satislari cekelim
    cursor.execute("SELECT product_id, quantity FROM sales")
    all_sales = cursor.fetchall()

    # Her urun icin toplam satilan miktari hesapla
    product_totals = {}
    for row in all_sales:
        pid = row[0]
        qty = row[1]
        if pid in product_totals:
            product_totals[pid] = product_totals[pid] + qty
        else:
            product_totals[pid] = qty

    # En cok satani bul
    top_pid = None
    top_qty = 0
    for pid in product_totals:
        if product_totals[pid] > top_qty:
            top_qty = product_totals[pid]
            top_pid = pid

    # Eger hic satis yoksa
    if top_pid is None:
        conn.close()
        return total_revenue, total_sales_count, "No sales yet", 0

    # En cok satan urunun ismini al
    cursor.execute("SELECT product_name FROM products WHERE product_id = ?", (top_pid,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return total_revenue, total_sales_count, row[0], top_qty
    else:
        return total_revenue, total_sales_count, "No sales yet", 0


def record_sale(product_id, quantity, sold_by=None):
    # Yeni satis kaydet
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()

    # Once urun bilgilerini al
    cursor.execute(
        "SELECT price, stock_quantity FROM products WHERE product_id = ?",
        (product_id,),
    )
    product = cursor.fetchone()

    if not product:
        conn.close()
        return "Product not found"

    price = product[0]
    stock = product[1]

    # Stok kontrolu
    if quantity > stock:
        conn.close()
        return "Not enough stock"

    # Toplam fiyati hesapla
    total = price * quantity
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Satisi kaydet
    cursor.execute(
        "INSERT INTO sales (product_id, quantity, total_price, sale_date, sold_by) VALUES (?, ?, ?, ?, ?)",
        (product_id, quantity, total, date, sold_by),
    )

    # Stoktan dus
    cursor.execute(
        "UPDATE products SET stock_quantity = stock_quantity - ? WHERE product_id = ?",
        (quantity, product_id),
    )

    conn.commit()
    conn.close()
    return "Sale recorded successfully"


def cancel_sale(sale_id):
    # Satisi iptal et, stogu geri yukle
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()

    cursor.execute("SELECT product_id, quantity FROM sales WHERE sale_id = ?", (sale_id,))
    sale = cursor.fetchone()

    if not sale:
        conn.close()
        return "Sale not found"

    product_id = sale[0]
    quantity = sale[1]

    # Stogu geri ekle
    cursor.execute(
        "UPDATE products SET stock_quantity = stock_quantity + ? WHERE product_id = ?",
        (quantity, product_id),
    )

    # Satisi sil
    cursor.execute("DELETE FROM sales WHERE sale_id = ?", (sale_id,))

    conn.commit()
    conn.close()
    return "Sale cancelled successfully"
