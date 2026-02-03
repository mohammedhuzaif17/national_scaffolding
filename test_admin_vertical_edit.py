#!/usr/bin/env python3
from app import app
from models import Product

print('Starting admin edit route test')

with app.test_client() as client:
    # Set up admin session
    with client.session_transaction() as sess:
        sess['user_type'] = 'admin'
    resp = client.get('/admin/vertical/161/edit')
    print('Status:', resp.status_code)
    print('Content type:', resp.content_type)
    data = resp.data.decode('utf-8')
    print('Response length:', len(data))
    # Print a slice to avoid huge output
    print(data[:1000])
    
    # If 500, print full
    if resp.status_code >= 400:
        print('\n===== FULL RESPONSE =====\n')
        print(data)
