#!/usr/bin/env python3
from app import app
from models import Admin, Order
from flask_login import login_user

with app.app_context():
    admin = Admin.query.first()
    print('Using admin:', admin.username if admin else 'NONE')

with app.test_client() as client:
    with client.session_transaction() as sess:
        sess['user_type'] = 'admin'
        sess['panel_type'] = 'scaffolding'
    resp = client.get('/admin_orders')
    print('Status:', resp.status_code)
    data = resp.data.decode('utf-8')
    # Count occurrences of order-card or similar marker
    count = data.count('order-card')
    print('Approx order cards found in HTML:', count)
