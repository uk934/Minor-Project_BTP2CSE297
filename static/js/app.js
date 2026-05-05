document.addEventListener('DOMContentLoaded', () => {
    initParticles();
    fetchProducts();
    
    document.getElementById('budget').addEventListener('change', () => {
        renderCart(); // Re-check budget warnings
        fetchRecommendations();
    });
    document.getElementById('checkoutBtn').addEventListener('click', openAddressModal);
    document.getElementById('search-input').addEventListener('input', filterProducts);
});

let products = [];
let cart = {}; // { product_id: quantity }
let currentCategory = 'All';

async function fetchProducts() {
    const res = await fetch('/api/products');
    products = await res.json();
    renderCategories();
    renderProducts();
}

function renderCategories() {
    const list = document.getElementById('category-list');
    const categories = ['All', ...new Set(products.map(p => p.category))];
    
    list.innerHTML = '';
    categories.forEach(cat => {
        const li = document.createElement('li');
        li.innerText = cat;
        if (cat === currentCategory) li.classList.add('active');
        
        li.onclick = () => {
            currentCategory = cat;
            document.querySelectorAll('#category-list li').forEach(el => el.classList.remove('active'));
            li.classList.add('active');
            document.getElementById('current-category-title').innerText = cat === 'All' ? 'All Products' : cat;
            renderProducts();
        };
        list.appendChild(li);
    });
}

function filterProducts() {
    const query = document.getElementById('search-input').value.toLowerCase();
    renderProducts(query);
}

function renderProducts(searchQuery = '') {
    const grid = document.getElementById('products-grid');
    grid.innerHTML = '';
    
    const filtered = products.filter(p => {
        const matchCat = currentCategory === 'All' || p.category === currentCategory;
        const matchSearch = p.name.toLowerCase().includes(searchQuery);
        return matchCat && matchSearch;
    });
    
    filtered.forEach(p => {
        const card = document.createElement('div');
        card.className = 'floating-card';
        card.style.animationDelay = `${Math.random() * 2}s`;
        
        const qty = cart[p.id] || 0;
        
        let controlHtml = '';
        if (qty === 0) {
            controlHtml = `<button class="btn-add" onclick="updateCart(${p.id}, 1)">ADD</button>`;
        } else {
            controlHtml = `
                <div class="qty-control">
                    <button class="qty-btn" onclick="updateCart(${p.id}, -1)">-</button>
                    <span class="qty-val">${qty}</span>
                    <button class="qty-btn" onclick="updateCart(${p.id}, 1)">+</button>
                </div>
            `;
        }
        
        card.innerHTML = `
            <div class="icon">${p.icon}</div>
            <div class="info">
                <div class="name">${p.name}</div>
                <div class="price">$${p.price.toFixed(2)}</div>
            </div>
            <div class="add-control">
                ${controlHtml}
            </div>
        `;
        
        grid.appendChild(card);
    });
}

function updateCart(id, change) {
    if (!cart[id]) cart[id] = 0;
    cart[id] += change;
    
    if (cart[id] <= 0) {
        delete cart[id];
    }
    
    renderProducts(); // Re-render to update Add buttons
    renderCart();
    fetchRecommendations();
}

function renderCart() {
    const list = document.getElementById('cart-list');
    const totalEl = document.getElementById('total-price');
    const countEl = document.getElementById('cart-item-count');
    
    list.innerHTML = '';
    
    const itemIds = Object.keys(cart);
    let totalItems = 0;
    let totalPrice = 0;
    
    if(itemIds.length === 0) {
        list.innerHTML = '<li class="empty-msg">Your cart is empty</li>';
        totalEl.innerText = '0.00';
        countEl.innerText = '0 items';
        return;
    }
    
    itemIds.forEach(idStr => {
        const id = parseInt(idStr);
        const qty = cart[id];
        const p = products.find(x => x.id === id);
        if(!p) return;
        
        totalItems += qty;
        totalPrice += (p.price * qty);
        
        const li = document.createElement('li');
        li.innerHTML = `
            <div class="cart-item-details">
                <span class="icon">${p.icon}</span>
                <div class="cart-item-info">
                    <span class="cart-item-name">${p.name}</span>
                    <span class="cart-item-price">$${p.price.toFixed(2)}</span>
                </div>
            </div>
            <div class="cart-item-actions">
                <button onclick="updateCart(${id}, -1)">-</button>
                <span>${qty}</span>
                <button onclick="updateCart(${id}, 1)">+</button>
            </div>
        `;
        list.appendChild(li);
    });
    
    countEl.innerText = `${totalItems} item${totalItems !== 1 ? 's' : ''}`;
    totalEl.innerText = totalPrice.toFixed(2);
    
    // Budget checking logic
    const budget = parseFloat(document.getElementById('budget').value) || 0;
    const warningEl = document.getElementById('budget-warning');
    const checkoutBtn = document.getElementById('checkoutBtn');
    
    if (totalPrice > budget) {
        warningEl.style.display = 'block';
        checkoutBtn.disabled = true;
        checkoutBtn.style.opacity = '0.5';
        checkoutBtn.style.cursor = 'not-allowed';
    } else {
        warningEl.style.display = 'none';
        checkoutBtn.disabled = false;
        checkoutBtn.style.opacity = '1';
        checkoutBtn.style.cursor = 'pointer';
    }
}

// Convert cart object to list of item IDs based on quantity for Apriori backend
function getCartArray() {
    const arr = [];
    for (const [id, qty] of Object.entries(cart)) {
        for (let i = 0; i < qty; i++) {
            arr.push(parseInt(id));
        }
    }
    return arr;
}

// Get unique cart IDs for recommendation request (since Apriori uses sets)
function getUniqueCartArray() {
    return Object.keys(cart).map(Number);
}

async function fetchRecommendations() {
    // Calculate remaining budget
    let totalPrice = 0;
    for (const [id, qty] of Object.entries(cart)) {
        const p = products.find(x => x.id === parseInt(id));
        if (p) totalPrice += p.price * qty;
    }
    
    const maxBudget = parseFloat(document.getElementById('budget').value) || 0;
    const remainingBudget = Math.max(0, maxBudget - totalPrice);
    
    const uniqueItems = getUniqueCartArray();
    
    const res = await fetch('/api/recommendations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cart: uniqueItems, budget: remainingBudget })
    });
    const recs = await res.json();
    renderRecommendations(recs);
}

function renderRecommendations(recs) {
    const list = document.getElementById('recs-list');
    list.innerHTML = '';
    
    if(Object.keys(cart).length === 0) {
        list.innerHTML = '<li class="empty-msg">Add items to see magic</li>';
        return;
    }
    
    if(recs.length === 0) {
        list.innerHTML = '<li class="empty-msg">No suggestions under budget</li>';
        return;
    }
    
    recs.forEach(r => {
        const li = document.createElement('li');
        li.innerHTML = `
            <div class="rec-item">
                <div class="cart-item-details">
                    <span class="icon">${r.icon}</span>
                    <div class="cart-item-info">
                        <span class="cart-item-name">${r.name}</span>
                        <span class="cart-item-price">$${r.price.toFixed(2)}</span>
                    </div>
                </div>
                <button class="rec-add-btn" onclick="updateCart(${r.product_id}, 1)">ADD</button>
            </div>
        `;
        list.appendChild(li);
    });
}

function clearCart() {
    if (Object.keys(cart).length === 0) return;
    if (confirm("Are you sure you want to empty your cart?")) {
        cart = {};
        renderProducts();
        renderCart();
        fetchRecommendations();
    }
}

// Checkout Flow Logic
function openAddressModal() {
    const cartArr = getCartArray();
    if(cartArr.length === 0) return alert("Cart is empty!");
    document.getElementById('addressModal').style.display = 'flex';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

function proceedToPayment() {
    const name = document.getElementById('address-name').value;
    const phone = document.getElementById('address-phone').value;
    const details = document.getElementById('address-details').value;
    
    if (!name || !phone || !details) {
        alert("Please fill in all address details!");
        return;
    }
    
    closeModal('addressModal');
    
    const totalPrice = document.getElementById('total-price').innerText;
    document.getElementById('final-pay-amount').innerText = totalPrice;
    
    document.getElementById('paymentModal').style.display = 'flex';
}

function selectPayment(element, method) {
    document.querySelectorAll('.payment-card').forEach(el => el.classList.remove('selected'));
    element.classList.add('selected');
}

async function finalCheckout() {
    const cartArr = getCartArray();
    
    // Animate button
    const btn = document.querySelector('#paymentModal .primary-btn');
    const originalText = btn.innerText;
    btn.innerText = "Processing...";
    btn.disabled = true;
    
    try {
        const res = await fetch('/api/checkout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cart: cartArr })
        });
        
        if(res.ok) {
            setTimeout(() => {
                alert("Payment Successful! Your order is placed and the engine has optimized with new data.");
                closeModal('paymentModal');
                cart = {};
                renderProducts();
                renderCart();
                fetchRecommendations();
                
                // Reset UI
                btn.innerText = originalText;
                btn.disabled = false;
                document.getElementById('address-name').value = '';
                document.getElementById('address-phone').value = '';
                document.getElementById('address-details').value = '';
            }, 800); // Fake delay for realism
        }
    } catch (err) {
        alert("Error placing order");
        btn.innerText = originalText;
        btn.disabled = false;
    }
}

// Particle Background Logic (Lighter for light theme)
function initParticles() {
    const canvas = document.getElementById('particleCanvas');
    const ctx = canvas.getContext('2d');
    
    let w = canvas.width = window.innerWidth;
    let h = canvas.height = window.innerHeight;
    
    window.addEventListener('resize', () => {
        w = canvas.width = window.innerWidth;
        h = canvas.height = window.innerHeight;
    });
    
    const particles = [];
    for(let i = 0; i < 40; i++) {
        particles.push({
            x: Math.random() * w,
            y: Math.random() * h,
            r: Math.random() * 2 + 1,
            dx: (Math.random() - 0.5) * 0.3,
            dy: (Math.random() - 0.5) * 0.3,
            color: `rgba(12, 131, 31, ${Math.random() * 0.15})` // Blinkit green particles
        });
    }
    
    function animate() {
        requestAnimationFrame(animate);
        ctx.clearRect(0, 0, w, h);
        
        particles.forEach(p => {
            p.x += p.dx;
            p.y += p.dy;
            
            if(p.x < 0 || p.x > w) p.dx *= -1;
            if(p.y < 0 || p.y > h) p.dy *= -1;
            
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fillStyle = p.color;
            ctx.fill();
        });
    }
    
    animate();
}
