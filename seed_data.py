import random
import os
from werkzeug.security import generate_password_hash
from database import init_db, get_db_connection, DB_FILE

def seed_data():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    products = [
        ("Milk", "Dairy", 2.50, "🥛"),
        ("Bread", "Bakery", 2.00, "🍞"),
        ("Eggs", "Dairy", 3.00, "🥚"),
        ("Butter", "Dairy", 4.00, "🧈"),
        ("Cheese", "Dairy", 5.00, "🧀"),
        ("Apples", "Fruit", 1.50, "🍎"),
        ("Bananas", "Fruit", 1.20, "🍌"),
        ("Chicken", "Meat", 7.00, "🍗"),
        ("Beef", "Meat", 9.00, "🥩"),
        ("Rice", "Pantry", 3.50, "🍚"),
        ("Pasta", "Pantry", 2.20, "🍝"),
        ("Tomato Sauce", "Pantry", 2.80, "🥫"),
        ("Coffee", "Beverage", 6.00, "☕"),
        ("Tea", "Beverage", 4.50, "🍵"),
        ("Juice", "Beverage", 3.80, "🧃")
    ]

    for name, category, price, icon in products:
        cursor.execute("INSERT INTO products (name, category, price, icon) VALUES (?, ?, ?, ?)", (name, category, price, icon))

    password_hash = generate_password_hash("password123")
    cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("test_user", password_hash))
    user_id = cursor.lastrowid

    # Seed preferences (randomized between 0 and 1)
    product_ids = list(range(1, len(products) + 1))
    for p_id in product_ids:
        pref = random.uniform(0.1, 1.0)
        cursor.execute("INSERT INTO user_preferences (user_id, product_id, preference_score) VALUES (?, ?, ?)", (user_id, p_id, round(pref, 2)))

    # Seed transactions to build rules
    # Common patterns:
    # 1. Milk + Bread
    # 2. Pasta + Tomato Sauce
    # 3. Eggs + Butter + Bread
    # 4. Coffee + Milk
    
    dummy_transactions = []
    
    for _ in range(50):
        t = []
        rand_pattern = random.randint(1, 5)
        if rand_pattern == 1:
            t.extend([1, 2]) # Milk, Bread
            if random.random() > 0.5: t.append(4) # Butter
        elif rand_pattern == 2:
            t.extend([11, 12]) # Pasta, Tomato Sauce
            if random.random() > 0.5: t.append(5) # Cheese
        elif rand_pattern == 3:
            t.extend([2, 3, 4]) # Bread, Eggs, Butter
        elif rand_pattern == 4:
            t.extend([1, 13]) # Milk, Coffee
        else:
            # Random selection
            t = random.sample(product_ids, k=random.randint(2, 5))
            
        dummy_transactions.append(t)

    for t in dummy_transactions:
        cursor.execute("INSERT INTO transactions (user_id) VALUES (?)", (user_id,))
        t_id = cursor.lastrowid
        for p_id in set(t): # Unique items only
            cursor.execute("INSERT INTO transaction_items (transaction_id, product_id) VALUES (?, ?)", (t_id, p_id))

    conn.commit()
    conn.close()
    print("Database seeded successfully with dummy products and transactions.")

if __name__ == "__main__":
    seed_data()
