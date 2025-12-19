#!/usr/bin/env python3
import time
import urllib.request

time.sleep(5)

try:
    response = urllib.request.urlopen('http://127.0.0.1:5001/national_scaffoldings', timeout=10)
    html = response.read().decode('utf-8')
    
    print(f"Page loaded: {len(html)} bytes")
    
    # Count product cards
    cards = html.count('product-card')
    print(f"Product cards: {cards}")
    
    # Check for products-grid
    if 'products-grid' in html:
        print("products-grid: FOUND")
        # Find the section
        start = html.find('products-grid')
        section = html[start:start+2000]
        print(f"Section: {section[:500]}")
    else:
        print("products-grid: NOT FOUND")
        
    # Check for product names
    if 'Single Width' in html:
        print("Product names: FOUND")
    else:
        print("Product names: NOT FOUND")
        
except Exception as e:
    print(f"Error: {e}")
