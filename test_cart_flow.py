#!/usr/bin/env python
"""
Test cart persistence across requests
"""
from app import app, db
from models import Product, User

# Clean up old test user
with app.app_context():
    old_user = User.query.filter_by(username='carttest').first()
    if old_user:
        db.session.delete(old_user)
        db.session.commit()
    
    # Create fresh test user
    user = User(username='carttest', email='cart@test.com', full_name='Cart Tester', phone='1111111111')
    user.set_password('test123')
    db.session.add(user)
    db.session.commit()
    user_id = user.id
    print(f'Created test user: {user_id}')

# Test with cookies
with app.test_client(use_cookies=True) as c:
    # First, manually log in by setting session
    with c.session_transaction() as sess:
        sess['user_id'] = user_id
        sess.permanent = True
    
    print('\n1. Session after manual login:')
    with c.session_transaction() as sess:
        print(f'   user_id: {sess.get("user_id")}')
    
    # Add to cart
    print('\n2. Adding to cart (product_id=1)...')
    resp = c.post('/add_to_cart', json={
        'product_id': 1,
        'quantity': 2,
        'customization': {'type': 'test'}
    }, follow_redirects=False)
    print(f'   Response status: {resp.status_code}')
    if resp.status_code == 200:
        data = resp.get_json()
        print(f'   Response success: {data.get("success")}')
        print(f'   Cart count: {data.get("cart_count")}')
    
    # Check session after add_to_cart
    print('\n3. Session after add_to_cart:')
    with c.session_transaction() as sess:
        cart = sess.get('cart', [])
        print(f'   cart items count: {len(cart)}')
        if cart:
            print(f'   first item: {cart[0].get("product_name")}')
    
    # Now get cart page
    print('\n4. GET /cart...')
    resp = c.get('/cart', follow_redirects=False)
    print(f'   Response status: {resp.status_code}')
    
    # Check if items are in HTML
    print(f'   Contains "cart-item": {b"cart-item" in resp.data}')
    print(f'   Contains "Product": {b"Product" in resp.data}')
    if b'Your cart is empty' in resp.data:
        print('   ERROR: Cart says empty but session had items!')
    
    # Final session check
    print('\n5. Final session state:')
    with c.session_transaction() as sess:
        cart = sess.get('cart', [])
        print(f'   cart items count: {len(cart)}')
