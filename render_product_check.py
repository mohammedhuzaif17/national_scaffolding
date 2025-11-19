from flask import Flask, render_template_string
import os

app = Flask(__name__)

template_path = os.path.join('templates','product_detail.html')
if not os.path.exists(template_path):
    print('Template not found:', template_path)
    raise SystemExit(1)

class DummyProduct:
    def __init__(self):
        self.name = 'Test Product'
        self.image_url = '/static/uploads/test1.jpg,/static/uploads/test2.jpg'
        self.description = 'A test product'
        self.category = 'aluminium'
        self.price = 1000
        self.rent_price = 200
        self.deposit_amount = 100
        self.weight_per_unit = 5
        self.customization_options = {'pricing_matrix': {'0.7': {'2': {'buy': 1000, 'rent': 200, 'deposit': 50}}}}
        self.id = 1

with app.test_request_context('/'):
    try:
        from flask import render_template
        rendered = render_template('product_detail.html', product=DummyProduct(), current_user=None)
        print('Rendered OK')
    except Exception as e:
        print('Render error:')
        import traceback
        traceback.print_exc()
        raise
