from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
from werkzeug.security import check_password_hash, generate_password_hash
from database import get_all_products, save_transaction, get_user_preferences, set_user_preference, get_user_by_username, create_user, update_user_preference_increment
from recommendation import get_engine, init_engine

app = Flask(__name__)
app.secret_key = 'antigravity_secret_key_123'

def get_current_user_id():
    return session.get('user_id')

@app.route('/')
def index():
    if not get_current_user_id():
        return redirect(url_for('login'))
    return render_template('index.html', username=session.get('username'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = get_user_by_username(username)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password are required')
            return render_template('register.html')
            
        hashed_pw = generate_password_hash(password)
        user_id = create_user(username, hashed_pw)
        
        if user_id:
            session['user_id'] = user_id
            session['username'] = username
            return redirect(url_for('index'))
        else:
            flash('Username already exists')
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/products', methods=['GET'])
def get_products():
    if not get_current_user_id():
        return jsonify({"error": "Unauthorized"}), 401
    products = get_all_products()
    return jsonify(products)

@app.route('/api/recommendations', methods=['POST'])
def recommendations():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.json
    cart = data.get('cart', [])
    budget = float(data.get('budget', 50.0))
    
    engine = get_engine()
    recs = engine.get_recommendations(cart, user_id, budget)
    return jsonify(recs)

@app.route('/api/checkout', methods=['POST'])
def checkout():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.json
    cart = data.get('cart', [])
    if cart:
        save_transaction(user_id, cart)
        
        # Increase preference for purchased items
        unique_items = set(cart)
        for p_id in unique_items:
            update_user_preference_increment(user_id, p_id, 0.1)
            
        init_engine() # Retrain engine after new transaction
        return jsonify({"status": "success", "message": "Transaction saved and preferences updated!"})
    return jsonify({"status": "error", "message": "Cart is empty"}), 400

@app.route('/api/preferences', methods=['GET', 'POST'])
def preferences():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
        
    if request.method == 'GET':
        prefs = get_user_preferences(user_id)
        return jsonify(prefs)
    elif request.method == 'POST':
        data = request.json
        product_id = data.get('product_id')
        score = data.get('score')
        if product_id is not None and score is not None:
            set_user_preference(user_id, product_id, float(score))
            return jsonify({"status": "success"})
        return jsonify({"status": "error"}), 400

if __name__ == '__main__':
    # Initialize recommendation engine model on startup
    init_engine()
    app.run(debug=True)
