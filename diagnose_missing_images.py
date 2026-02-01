#!/usr/bin/env python3
"""
Diagnose missing images and show which cuplock products need images
"""

from app import app, db
from models import Product, CuplockVerticalSize, CuplockLedgerSize
import os

def diagnose():
    with app.app_context():
        print("\n" + "="*100)
        print("MISSING IMAGES DIAGNOSIS")
        print("="*100)
        
        # Get all cuplock products (vertical and ledger)
        cuplock_products = Product.query.filter(
            db.or_(
                db.and_(Product.category.ilike('%cuplock%'), Product.cuplock_type.ilike('%vertical%')),
                db.and_(Product.category.ilike('%cuplock%'), Product.cuplock_type.ilike('%ledger%'))
            )
        ).all()
        
        print(f"\nTotal Cuplock Products (vertical + ledger): {len(cuplock_products)}\n")
        
        missing_images = []
        
        for prod in cuplock_products:
            prod_type = prod.cuplock_type or "unknown"
            
            print(f"\nProduct ID: {prod.id} | Name: {prod.name} | Type: {prod_type} | Active: {prod.is_active}")
            print(f"  DB image_url: {prod.image_url}")
            
            if not prod.image_url:
                print(f"  ❌ NO IMAGE SET IN DATABASE")
                missing_images.append({
                    'id': prod.id,
                    'name': prod.name,
                    'reason': 'No image_url in database',
                    'type': prod_type
                })
            else:
                # Check if file exists
                images_str = prod.image_url
                image_list = [img.strip() for img in images_str.split(',')]
                
                for img_path in image_list:
                    # Normalize path
                    if img_path.startswith('static/'):
                        fs_path = img_path
                    elif img_path.startswith('/static/'):
                        fs_path = img_path[1:]  # Remove leading /
                    else:
                        fs_path = os.path.join('static', img_path)
                    
                    exists = os.path.exists(fs_path)
                    status = "✓" if exists else "❌"
                    print(f"  {status} {img_path}")
                    
                    if not exists:
                        missing_images.append({
                            'id': prod.id,
                            'name': prod.name,
                            'expected_path': img_path,
                            'reason': 'File not found on disk',
                            'type': prod_type,
                            'full_path': fs_path
                        })
            
            # Check sizes
            if prod_type == 'vertical':
                sizes = CuplockVerticalSize.query.filter_by(product_id=prod.id, is_active=True).all()
                print(f"  Sizes: {len(sizes)} active sizes")
                for sz in sizes:
                    print(f"    - {sz.size_label}: buy={sz.buy_price}, rent={sz.rent_price}, deposit={sz.deposit}")
            elif prod_type == 'ledger':
                sizes = CuplockLedgerSize.query.filter_by(product_id=prod.id, is_active=True).all()
                print(f"  Sizes: {len(sizes)} active sizes")
                for sz in sizes:
                    print(f"    - {sz.size_label}: buy={sz.buy_price}, rent={sz.rent_price}, deposit={sz.deposit_amount}")
        
        print("\n" + "="*100)
        print("SUMMARY OF MISSING IMAGES")
        print("="*100)
        
        if missing_images:
            print(f"\n⚠️  {len(missing_images)} ISSUE(S) FOUND:\n")
            for item in missing_images:
                print(f"  • Product ID {item['id']} ({item['name']})")
                print(f"    Reason: {item['reason']}")
                if 'expected_path' in item:
                    print(f"    Expected: {item['expected_path']}")
                    print(f"    Full FS path: {item['full_path']}")
                print()
        else:
            print("\n✓ ALL IMAGES PRESENT!")
        
        # List available uploads
        print("\n" + "="*100)
        print("AVAILABLE IMAGES IN static/uploads/")
        print("="*100)
        upload_dir = 'static/uploads'
        if os.path.exists(upload_dir):
            files = sorted(os.listdir(upload_dir))[:20]  # First 20
            print(f"\nShowing first 20 files (total: {len(os.listdir(upload_dir))}):\n")
            for f in files:
                print(f"  uploads/{f}")
        else:
            print("\n❌ static/uploads/ does not exist!")
        
        print("\n" + "="*100)
        print("SOLUTION OPTIONS:")
        print("="*100)
        print("""
1. Re-upload images for each product via the admin panel:
   - Go to /admin/vertical or /admin/ledger
   - Click edit on the product
   - Upload the image file
   - Save
   
2. Or manually update the database to point to existing images:
   - UPDATE products SET image_url='uploads/EXISTING_FILENAME.jpg' WHERE id=<product_id>;
   
3. Or get the 3 product IDs and I can help fix the image_url to existing files
        """)

if __name__ == '__main__':
    diagnose()
