from models import db, Product
from app import app

with app.app_context():
    products = Product.query.all()
    print(f'Total products: {len(products)}\n')
    for p in products:
        print(f'ID: {p.id} | Name: {p.name} | Type: {p.product_type} | Category: {p.category}')
