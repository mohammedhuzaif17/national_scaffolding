from app import app, db
from models import User, Admin, Product

def seed_database():
    with app.app_context():
        db.drop_all()
        db.create_all()
        
        admin_scaffolding = Admin(username='admin_scaffolding', panel_type='scaffolding')
        admin_scaffolding.set_password('admin123')
        db.session.add(admin_scaffolding)
        
        admin_fabrication = Admin(username='admin_fabrication', panel_type='fabrication')
        admin_fabrication.set_password('admin123')
        db.session.add(admin_fabrication)
        
        test_user = User(
            username='testuser',
            full_name='Test User',
            email='test@example.com',
            phone='9999999999',
            organization='Test Company'
        )
        test_user.set_password('test123')
        db.session.add(test_user)
        
        scaffolding_products = [
            Product(
                name='Aluminium H-Frame Scaffolding',
                price=2500,
                rent_price=500,
                description='High-quality aluminium H-frame scaffolding with customizable width (0.7m or 1.4m) and height options from 2m to 16m. Ideal for construction and maintenance work.',
                category='aluminium',
                product_type='scaffolding',
                weight_per_unit=25,
                customization_options={
                    'pricing_matrix': {
                        '0.7': {
                            '2': 2500, '3': 3200, '4': 3800, '5': 4500
                        },
                        '1.4': {
                            '2': 3500, '3': 4200, '4': 5000, '5': 5800,
                            '6': 6500, '7': 7200, '8': 8000, '9': 8800,
                            '10': 9500, '11': 10300, '12': 11000, '13': 11800,
                            '14': 12500, '15': 13300, '16': 14000
                        }
                    }
                }
            ),
            Product(
                name='Aluminium Mobile Tower',
                price=4500,
                rent_price=900,
                description='Portable aluminium mobile tower scaffolding with wheels. Easy to move and assemble. Perfect for indoor and outdoor projects.',
                category='aluminium',
                product_type='scaffolding',
                weight_per_unit=35,
                customization_options={
                    'pricing_matrix': {
                        '0.7': {
                            '2': 4500, '3': 5200, '4': 5800, '5': 6500
                        },
                        '1.4': {
                            '2': 5500, '3': 6200, '4': 7000, '5': 7800,
                            '6': 8500, '7': 9200, '8': 10000, '9': 10800,
                            '10': 11500, '11': 12300, '12': 13000
                        }
                    }
                }
            ),
            Product(
                name='H-Frame Standard Set',
                price=1800,
                description='Standard H-frame scaffolding set made from high-grade steel. Bulk discounts available: 10+ pieces get 5% off, 20+ get 7.5% off, 30-50 get 10% off, 50-100 get 12% off.',
                category='h-frames',
                product_type='scaffolding',
                weight_per_unit=30
            ),
            Product(
                name='H-Frame Heavy Duty',
                price=2200,
                description='Heavy-duty H-frame scaffolding for industrial applications. Supports higher loads. Bulk discounts apply automatically.',
                category='h-frames',
                product_type='scaffolding',
                weight_per_unit=40
            ),
            Product(
                name='Cuplock Vertical System',
                price=850,
                description='Cuplock vertical components available in 1m, 2m, and 3m sizes with 1-6 cups. Customizable length from 1.1m to 3.0m. Priced at ₹78 per kg.',
                category='cuplock',
                product_type='scaffolding',
                weight_per_unit=10.9
            ),
            Product(
                name='Cuplock Ledger System',
                price=780,
                description='Cuplock ledger components available in sizes from 0.6m to 3.0m. Professional-grade quality. Priced at ₹78 per kg.',
                category='cuplock',
                product_type='scaffolding',
                weight_per_unit=10
            ),
            Product(
                name='Safety Harness',
                price=1200,
                description='Full-body safety harness with adjustable straps. Essential safety equipment for working at heights.',
                category='accessories',
                product_type='scaffolding',
                weight_per_unit=2
            ),
            Product(
                name='Scaffolding Clamps',
                price=150,
                description='Heavy-duty scaffolding clamps for secure connections. Sold per piece.',
                category='accessories',
                product_type='scaffolding',
                weight_per_unit=0.5
            ),
            Product(
                name='Base Plates',
                price=450,
                description='Adjustable base plates for scaffolding stability on uneven surfaces.',
                category='accessories',
                product_type='scaffolding',
                weight_per_unit=3
            ),
            Product(
                name='Scaffolding Wheels',
                price=800,
                description='Durable wheels for mobile scaffolding systems. Set of 4 wheels.',
                category='accessories',
                product_type='scaffolding',
                weight_per_unit=5
            ),
        ]
        
        fabrication_products = [
            Product(
                name='Custom Steel Sofa Frame',
                price=8500,
                description='Custom-made steel sofa frame with powder coating finish',
                product_type='fabrication'
            ),
            Product(
                name='Dining Table Frame',
                price=12000,
                description='Modern dining table frame fabricated from premium steel',
                product_type='fabrication'
            ),
            Product(
                name='Steel Shelf Unit',
                price=5500,
                description='Industrial-style steel shelf unit for home or office',
                product_type='fabrication'
            ),
        ]
        
        db.session.add_all(scaffolding_products + fabrication_products)
        db.session.commit()
        
        print("Database seeded successfully!")
        print("\nAdmin Credentials:")
        print("Scaffolding Admin - Username: admin_scaffolding, Password: admin123")
        print("Fabrication Admin - Username: admin_fabrication, Password: admin123")
        print("\nTest User - Username: testuser, Password: test123")

if __name__ == '__main__':
    seed_database()
