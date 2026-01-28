#!/usr/bin/env python
"""
Find products with missing image files and replace with best-match from static/uploads
"""
import os
from app import app, db
from models import Product

UPLOADS_DIR = os.path.join(app.static_folder, 'uploads')

def find_best_match(original_name, product):
    # Lowercase for matching
    orig = original_name.lower()
    # common keywords from product name and type
    keywords = []
    if product.name:
        keywords += [w for w in product.name.lower().split() if len(w) > 3]
    if product.cuplock_type:
        keywords.append(product.cuplock_type.lower())
    # also include 'vertical'/'ledger' tokens if present in original name
    if 'vertical' in orig:
        keywords.append('vertical')
    if 'ledger' in orig:
        keywords.append('ledger')

    # Collect candidate files
    try:
        files = os.listdir(UPLOADS_DIR)
    except Exception:
        return None

    # First try exact substring match of suffix (e.g., 'vertical')
    for f in files:
        lf = f.lower()
        if any(k in lf for k in keywords) and lf.endswith(('.jpg', '.jpeg', '.png', '.webp')):
            return f

    # Fallback: return first image in uploads directory
    return files[0] if files else None


def main():
    changed = []
    with app.app_context():
        products = Product.query.all()
        for p in products:
            if not p.image_url:
                continue
            first_image = p.image_url.split(',')[0].strip()
            # Normalize path: remove leading /static/
            if first_image.startswith('/static/'):
                rel = first_image[len('/static/'):]
            else:
                rel = first_image.lstrip('/')
            file_path = os.path.join(app.static_folder, rel)
            if os.path.exists(file_path):
                # exists, skip
                continue
            # file missing - attempt to find replacement
            best = find_best_match(rel, p)
            if best:
                new_path = f"uploads/{best}"
                print(f"Updating Product {p.id} '{p.name}': {rel} -> {new_path}")
                p.image_url = new_path
                changed.append((p.id, rel, new_path))
            else:
                print(f"No candidate for Product {p.id} '{p.name}' (missing {rel})")

        if changed:
            db.session.commit()
            print(f"\nCommitted {len(changed)} changes.")
        else:
            print("No changes needed.")

if __name__ == '__main__':
    main()
