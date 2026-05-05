import sqlite3
import os

DB_FILE = "grocery.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create Products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            icon TEXT
        )
    ''')

    # Create Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
    ''')

    # Create Transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Create TransactionItems table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transaction_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id INTEGER,
            product_id INTEGER,
            FOREIGN KEY (transaction_id) REFERENCES transactions (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')

    # Create UserPreferences table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            user_id INTEGER,
            product_id INTEGER,
            preference_score REAL NOT NULL,
            PRIMARY KEY (user_id, product_id),
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')

    conn.commit()
    conn.close()

def get_all_products():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return products

def get_product_by_id(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id=?", (product_id,))
    product = cursor.fetchone()
    conn.close()
    return dict(product) if product else None

def get_user_preferences(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT product_id, preference_score FROM user_preferences WHERE user_id=?", (user_id,))
    prefs = {row['product_id']: row['preference_score'] for row in cursor.fetchall()}
    conn.close()
    return prefs

def get_all_transactions():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.id as transaction_id, ti.product_id
        FROM transactions t
        JOIN transaction_items ti ON t.id = ti.transaction_id
    """)
    rows = cursor.fetchall()
    conn.close()
    
    # Format into list of lists (transactions)
    transactions_dict = {}
    for row in rows:
        t_id = row['transaction_id']
        p_id = row['product_id']
        if t_id not in transactions_dict:
            transactions_dict[t_id] = []
        transactions_dict[t_id].append(p_id)
        
    return list(transactions_dict.values())

def save_transaction(user_id, product_ids):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO transactions (user_id) VALUES (?)", (user_id,))
    t_id = cursor.lastrowid
    
    for p_id in product_ids:
        cursor.execute("INSERT INTO transaction_items (transaction_id, product_id) VALUES (?, ?)", (t_id, p_id))
    
    conn.commit()
    conn.close()
    return t_id

def set_user_preference(user_id, product_id, score):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Upsert
    cursor.execute("""
        INSERT INTO user_preferences (user_id, product_id, preference_score)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, product_id) DO UPDATE SET preference_score=excluded.preference_score
    """, (user_id, product_id, score))
    conn.commit()
    conn.close()

def update_user_preference_increment(user_id, product_id, increment=0.1):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT preference_score FROM user_preferences WHERE user_id=? AND product_id=?", (user_id, product_id))
    row = cursor.fetchone()
    
    if row:
        new_score = min(1.0, row['preference_score'] + increment)
        cursor.execute("UPDATE user_preferences SET preference_score=? WHERE user_id=? AND product_id=?", (new_score, user_id, product_id))
    else:
        new_score = min(1.0, 0.5 + increment) # Base score is 0.5
        cursor.execute("INSERT INTO user_preferences (user_id, product_id, preference_score) VALUES (?, ?, ?)", (user_id, product_id, new_score))
        
    conn.commit()
    conn.close()

def get_user_by_username(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def create_user(username, password_hash):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
        conn.commit()
        user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        user_id = None
    conn.close()
    return user_id

if __name__ == "__main__":
    init_db()
