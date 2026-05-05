# Smart Grocery Recommendation App

This is a Flask-based web application implementing an optimized grocery recommendation system based on Frequent Pattern Mining (Apriori Algorithm) with an Antigravity UI.

## Features
- Real-time recommendations based on cart items using Apriori association rules.
- Optimization Layer: Considers purchase frequency, user preference, and item cost.
- Budget filtering: Hides recommendations that exceed the defined budget.
- Antigravity Theme: Floating animations, particle background, modern glassmorphism UI.

## Setup
1. Create a virtual environment: `python -m venv venv`
2. Activate it: `venv\Scripts\activate` (Windows)
3. Install dependencies: `pip install -r requirements.txt`
4. Seed the database: `python seed_data.py`
5. Run the server: `python app.py`

Open your browser at `http://127.0.0.1:5000`
