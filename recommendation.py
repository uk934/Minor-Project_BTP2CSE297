import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules
from database import get_all_transactions, get_all_products, get_user_preferences

class RecommendationEngine:
    def __init__(self, alpha=0.4, beta=0.4, gamma=0.2):
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.rules = None
        self.frequent_itemsets = None
        self.item_supports = {}
        self.max_price = 1.0
        self.products_df = None
        
        self.train_model()

    def train_model(self):
        transactions = get_all_transactions()
        if not transactions:
            return
            
        # Convert list of lists of product_ids into a binary matrix
        te = TransactionEncoder()
        te_ary = te.fit(transactions).transform(transactions)
        df = pd.DataFrame(te_ary, columns=te.columns_)

        # Apriori
        self.frequent_itemsets = apriori(df, min_support=0.05, use_colnames=True)
        
        # Calculate item supports for F(i)
        for idx, row in self.frequent_itemsets.iterrows():
            itemset = list(row['itemsets'])
            if len(itemset) == 1:
                self.item_supports[itemset[0]] = row['support']
        
        # Association Rules
        if not self.frequent_itemsets.empty:
            self.rules = association_rules(self.frequent_itemsets, metric="confidence", min_threshold=0.1)
        
        products = get_all_products()
        self.products_df = pd.DataFrame(products)
        if not self.products_df.empty:
            self.max_price = self.products_df['price'].max()

    def get_recommendations(self, cart_item_ids, user_id, budget):
        if self.rules is None or self.rules.empty or not cart_item_ids:
            return []

        cart_set = frozenset(cart_item_ids)
        
        # Find matching rules where antecedent is a subset of the cart
        matching_rules = self.rules[self.rules['antecedents'].apply(lambda x: x.issubset(cart_set))]
        
        recommended_items = set()
        for consequents in matching_rules['consequents']:
            for item in consequents:
                if item not in cart_set:
                    recommended_items.add(item)
                    
        # Apply Optimization Layer
        # S(i) = α·F(i) + β·P(i) − γ·C(i)
        
        preferences = get_user_preferences(user_id)
        
        scored_recommendations = []
        for item_id in recommended_items:
            # Get product details
            product_row = self.products_df[self.products_df['id'] == item_id]
            if product_row.empty:
                continue
                
            price = product_row.iloc[0]['price']
            
            # Filter by budget
            if price > budget:
                continue
                
            # Calculate factors
            f_i = self.item_supports.get(item_id, 0)
            p_i = preferences.get(item_id, 0.5) # Default preference if not set
            c_i = price / self.max_price if self.max_price > 0 else 0
            
            # Optimization score
            s_i = (self.alpha * f_i) + (self.beta * p_i) - (self.gamma * c_i)
            
            scored_recommendations.append({
                'product_id': int(item_id),
                'name': product_row.iloc[0]['name'],
                'price': float(price),
                'icon': product_row.iloc[0]['icon'],
                'score': float(s_i),
                'support': float(f_i),
                'confidence_related': float(matching_rules[matching_rules['consequents'].apply(lambda x: item_id in x)]['confidence'].max())
            })
            
        # Sort by score descending
        scored_recommendations.sort(key=lambda x: x['score'], reverse=True)
        return scored_recommendations

# Global instance
engine = None

def init_engine():
    global engine
    engine = RecommendationEngine()
    return engine

def get_engine():
    global engine
    if engine is None:
        init_engine()
    return engine
