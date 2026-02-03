#!/usr/bin/env python3
import traceback
from app import app
from models import Product

print('Testing latest vertical product public page')

with app.app_context():
    prod = Product.query.filter(Product.cuplock_type.ilike('vertical')).order_by(Product.id.desc()).first()
    if not prod:
        print('No vertical product found')
    else:
        print(f'Latest vertical product: id={prod.id}, name={prod.name}, is_active={prod.is_active}, image_url={prod.image_url}')

with app.test_client() as client:
    if not prod:
        print('Skipping GET because no product')
    else:
        try:
            resp = client.get(f'/product/vertical/{prod.id}')
            print('GET status:', resp.status_code)
            print('Content-Type:', resp.content_type)
            data = resp.data.decode('utf-8', errors='replace')
            print('Response length:', len(data))
            print('--- Response preview ---')
            print(data[:1000])
        except Exception:
            print('Exception during GET:')
            traceback.print_exc()

        # Also try calling the view directly to capture exception
        try:
            from cuplock_routes import vertical_product_page
            with app.test_request_context(f'/product/vertical/{prod.id}'):
                rv = vertical_product_page(prod.id)
                print('Direct call returned type:', type(rv))
        except Exception:
            print('Exception during direct call:')
            traceback.print_exc()
