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
        
        test_user = User(username='testuser', email='test@example.com')
        test_user.set_password('test123')
        db.session.add(test_user)
        
        scaffolding_products = [
            Product(
                name='Aluminium H-Frame (Customizable)',
                price=2500,
                rent_price=500,
                description='High-quality aluminium H-frame scaffolding with customizable width and height options',
                category='aluminium',
                product_type='scaffolding'
            ),
            Product(
                name='Cuplock System Standard',
                price=3200,
                rent_price=650,
                description='Professional cuplock scaffolding system for heavy-duty construction',
                category='cuplock',
                product_type='scaffolding'
            ),
            Product(
                name='Aluminium Mobile Tower',
                price=4500,
                rent_price=900,
                description='Portable aluminium mobile tower scaffolding, easy to move and assemble',
                category='aluminium',
                product_type='scaffolding'
            ),
            Product(
                name='H-Frame Standard Set',
                price=1800,
                rent_price=350,
                description='Standard H-frame scaffolding set with bulk discount options',
                category='h-frames',
                product_type='scaffolding'
            ),
            Product(
                name='Cuplock Vertical (1-6 cups)',
                price=850,
                description='Cuplock vertical components available in various sizes',
                category='cuplock',
                product_type='scaffolding'
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
