#!/usr/bin/env python
"""
Script to fix image URLs in the database.
Converts absolute paths like '/static/uploads/...' to relative paths like 'uploads/...'
"""

from models import db, Product
from app import app
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_image_urls():
    """Fix image URLs in the database."""
    with app.app_context():
        try:
            # Get all products with image URLs
            products = Product.query.filter(Product.image_url.isnot(None)).all()
            
            updated_count = 0
            for product in products:
                if product.image_url:
                    # Replace ALL occurrences of /static/ with nothing
                    if '/static/' in product.image_url:
                        old_url = product.image_url
                        new_url = product.image_url.replace('/static/', '')
                        
                        product.image_url = new_url
                        updated_count += 1
                        
                        logger.info(f"Product {product.id} ({product.name})")
                        logger.info(f"  Old: {old_url}")
                        logger.info(f"  New: {new_url}")
            
            if updated_count > 0:
                db.session.commit()
                logger.info(f"\nFixed {updated_count} product image URLs successfully!")
            else:
                logger.info("No products with /static/ paths found - database already correct!")
                
        except Exception as e:
            logger.error(f"Error fixing image URLs: {e}")
            db.session.rollback()

if __name__ == '__main__':
    fix_image_urls()
