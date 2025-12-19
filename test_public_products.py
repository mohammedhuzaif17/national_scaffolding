#!/usr/bin/env python3
"""Test that products display when not logged in"""

import urllib.request
import time

time.sleep(3)

# Test the homepage products
try:
    with urllib.request.urlopen('http://127.0.0.1:5001/national_scaffoldings', timeout=5) as resp:
        html = resp.read().decode('utf-8')
        print(f'Response status: 200')
        
        # Count product cards
        product_cards = html.count('<div class="product-card">')
        print(f'Product cards found: {product_cards}')
        
        # Check for specific products  
        has_products = 'product-card' in html
        print(f'Has products: {has_products}')
        
        # Sample of product names
        if 'Single Width' in html:
            print('Found "Single Width" product')
        elif 'Cuplock' in html:
            print('Found "Cuplock" product')
        elif 'product' in html.lower():
            print('Found products in HTML')
        
        if product_cards > 50:
            print(f'\nSUCCESS: {product_cards} products displaying!')
        else:
            print(f'\nISSUE: Only {product_cards} products found')
except Exception as e:
    print(f'Error: {e}')
