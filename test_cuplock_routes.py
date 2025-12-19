"""
Comprehensive test suite for cuplock_routes.py
Tests all major functionality including:
- Product creation (vertical and ledger)
- Image upload handling
- Product editing
- Product deletion
- Size/configuration management
- Customer-facing product pages
"""

import unittest
import os
import tempfile
import json
from io import BytesIO
from flask import session, url_for
from app import app, db
from models import Product, CuplockVerticalSize, CuplockLedgerSize, CuplockVerticalCup, Admin
from werkzeug.datastructures import FileStorage


class CuplockRoutesTestCase(unittest.TestCase):
    """Test suite for Cuplock Routes"""
    
    def setUp(self):
        """Set up test client and database"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['WTF_CSRF_ENABLED'] = False
        
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            self.create_test_admin()
    
    def tearDown(self):
        """Clean up after tests"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def create_test_admin(self):
        """Create a test admin user"""
        admin = Admin(
            username='admin',
            panel_type='cuplock'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
    
    def login_as_admin(self):
        """Set up session as admin"""
        with self.client.session_transaction() as sess:
            sess['admin_id'] = 1
            sess['user_type'] = 'admin'
    
    def create_dummy_image(self):
        """Create a dummy image file for testing"""
        img = BytesIO()
        img.write(b'GIF89a')
        img.seek(0)
        img.name = 'test.gif'
        return FileStorage(
            stream=img,
            filename='test.gif',
            content_type='image/gif'
        )
    
    # =========================================
    # TEST CASE 1: Vertical Product Creation
    # =========================================
    def test_vertical_create_product_success(self):
        """Test: Create vertical Cuplock product successfully"""
        self.login_as_admin()
        
        response = self.client.post('/cuplock/admin/vertical/create', data={
            'name': 'Test Vertical Product',
            'description': 'Test Description',
            'price': '100.00'
        }, follow_redirects=True)
        
        # Check product was created
        with self.app.app_context():
            product = Product.query.filter_by(name='Test Vertical Product').first()
            self.assertIsNotNone(product)
            self.assertEqual(product.category, 'cuplock')
            self.assertEqual(product.cuplock_type, 'vertical')
            self.assertEqual(product.price, 100.0)
            self.assertTrue(product.is_active)
        
        print("✓ TEST PASSED: Vertical product creation")
    
    def test_vertical_create_with_image(self):
        """Test: Create vertical product with image upload"""
        self.login_as_admin()
        
        response = self.client.post('/cuplock/admin/vertical/create', 
            data={
                'name': 'Vertical With Image',
                'description': 'With image',
                'price': '150.00',
                'image': self.create_dummy_image()
            },
            content_type='multipart/form-data',
            follow_redirects=True
        )
        
        with self.app.app_context():
            product = Product.query.filter_by(name='Vertical With Image').first()
            self.assertIsNotNone(product)
            self.assertIsNotNone(product.image_url)
            self.assertIn('.gif', product.image_url)
        
        print("✓ TEST PASSED: Vertical product creation with image")
    
    def test_vertical_create_missing_name(self):
        """Test: Create vertical product without required name"""
        self.login_as_admin()
        
        response = self.client.post('/cuplock/admin/vertical/create', data={
            'description': 'No name provided',
            'price': '100.00'
        }, follow_redirects=True)
        
        with self.app.app_context():
            count = Product.query.filter_by(description='No name provided').count()
            self.assertEqual(count, 0)
        
        print("✓ TEST PASSED: Vertical product creation validation (missing name)")
    
    def test_vertical_create_invalid_price(self):
        """Test: Create vertical product with invalid price format"""
        self.login_as_admin()
        
        response = self.client.post('/cuplock/admin/vertical/create', data={
            'name': 'Invalid Price Product',
            'description': 'Invalid price',
            'price': 'invalid'
        }, follow_redirects=True)
        
        with self.app.app_context():
            product = Product.query.filter_by(name='Invalid Price Product').first()
            self.assertIsNotNone(product)
            self.assertEqual(product.price, 0.0)  # Should default to 0
        
        print("✓ TEST PASSED: Vertical product handles invalid price")
    
    # =========================================
    # TEST CASE 2: Ledger Product Creation
    # =========================================
    def test_ledger_create_product_success(self):
        """Test: Create ledger Cuplock product successfully"""
        self.login_as_admin()
        
        response = self.client.post('/cuplock/admin/ledger/create', data={
            'name': 'Test Ledger Product',
            'description': 'Ledger Description',
            'price': '200.00'
        }, follow_redirects=True)
        
        with self.app.app_context():
            product = Product.query.filter_by(name='Test Ledger Product').first()
            self.assertIsNotNone(product)
            self.assertEqual(product.category, 'cuplock')
            self.assertEqual(product.cuplock_type, 'ledger')
            self.assertEqual(product.price, 200.0)
            self.assertTrue(product.is_active)
        
        print("✓ TEST PASSED: Ledger product creation")
    
    def test_ledger_create_with_image(self):
        """Test: Create ledger product with image upload"""
        self.login_as_admin()
        
        response = self.client.post('/cuplock/admin/ledger/create',
            data={
                'name': 'Ledger With Image',
                'description': 'With image',
                'price': '250.00',
                'image': self.create_dummy_image()
            },
            content_type='multipart/form-data',
            follow_redirects=True
        )
        
        with self.app.app_context():
            product = Product.query.filter_by(name='Ledger With Image').first()
            self.assertIsNotNone(product)
            self.assertIsNotNone(product.image_url)
        
        print("✓ TEST PASSED: Ledger product creation with image")
    
    # =========================================
    # TEST CASE 3: Product Editing
    # =========================================
    def test_vertical_edit_product(self):
        """Test: Edit vertical product"""
        self.login_as_admin()
        
        # Create product first
        with self.app.app_context():
            product = Product(
                name='Original Name',
                description='Original Description',
                category='cuplock',
                cuplock_type='vertical',
                product_type='scaffolding',
                price=100.0,
                is_active=True
            )
            db.session.add(product)
            db.session.commit()
            product_id = product.id
        
        # Edit the product
        response = self.client.post(f'/cuplock/admin/vertical/{product_id}/edit', data={
            'name': 'Updated Name',
            'description': 'Updated Description'
        }, follow_redirects=True)
        
        with self.app.app_context():
            product = Product.query.get(product_id)
            self.assertEqual(product.name, 'Updated Name')
            self.assertEqual(product.description, 'Updated Description')
        
        print("✓ TEST PASSED: Vertical product editing")
    
    def test_ledger_edit_product(self):
        """Test: Edit ledger product"""
        self.login_as_admin()
        
        with self.app.app_context():
            product = Product(
                name='Ledger Original',
                description='Original',
                category='cuplock',
                cuplock_type='ledger',
                product_type='scaffolding',
                price=200.0,
                is_active=True
            )
            db.session.add(product)
            db.session.commit()
            product_id = product.id
        
        response = self.client.post(f'/cuplock/admin/ledger/{product_id}/edit', data={
            'name': 'Ledger Updated',
            'description': 'Updated'
        }, follow_redirects=True)
        
        with self.app.app_context():
            product = Product.query.get(product_id)
            self.assertEqual(product.name, 'Ledger Updated')
        
        print("✓ TEST PASSED: Ledger product editing")
    
    # =========================================
    # TEST CASE 4: Product Deletion
    # =========================================
    def test_vertical_delete_product(self):
        """Test: Soft delete vertical product"""
        self.login_as_admin()
        
        with self.app.app_context():
            product = Product(
                name='To Delete',
                category='cuplock',
                cuplock_type='vertical',
                product_type='scaffolding',
                price=100.0,
                is_active=True
            )
            db.session.add(product)
            db.session.commit()
            product_id = product.id
        
        response = self.client.post(f'/cuplock/admin/vertical/product/{product_id}/delete')
        data = json.loads(response.data)
        
        self.assertTrue(data['success'])
        
        with self.app.app_context():
            product = Product.query.get(product_id)
            self.assertFalse(product.is_active)
        
        print("✓ TEST PASSED: Vertical product deletion (soft delete)")
    
    def test_ledger_delete_product(self):
        """Test: Soft delete ledger product"""
        self.login_as_admin()
        
        with self.app.app_context():
            product = Product(
                name='Ledger To Delete',
                category='cuplock',
                cuplock_type='ledger',
                product_type='scaffolding',
                price=200.0,
                is_active=True
            )
            db.session.add(product)
            db.session.commit()
            product_id = product.id
        
        response = self.client.post(f'/cuplock/admin/ledger/product/{product_id}/delete')
        data = json.loads(response.data)
        
        self.assertTrue(data['success'])
        
        with self.app.app_context():
            product = Product.query.get(product_id)
            self.assertFalse(product.is_active)
        
        print("✓ TEST PASSED: Ledger product deletion (soft delete)")
    
    # =========================================
    # TEST CASE 5: Size Management
    # =========================================
    def test_add_vertical_size(self):
        """Test: Add size to vertical product"""
        self.login_as_admin()
        
        with self.app.app_context():
            product = Product(
                name='Vertical Product',
                category='cuplock',
                cuplock_type='vertical',
                product_type='scaffolding',
                price=100.0,
                is_active=True
            )
            db.session.add(product)
            db.session.commit()
            product_id = product.id
        
        response = self.client.post(f'/cuplock/admin/vertical/{product_id}/size/add', data={
            'size_label': '1m',
            'weight': '2.5',
            'buy_price': '100',
            'rent_price': '10',
            'deposit': '500'
        })
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        with self.app.app_context():
            size = CuplockVerticalSize.query.filter_by(
                product_id=product_id,
                size_label='1m'
            ).first()
            self.assertIsNotNone(size)
            self.assertEqual(size.weight, 2.5)
        
        print("✓ TEST PASSED: Add vertical size")
    
    def test_add_ledger_size(self):
        """Test: Add size to ledger product"""
        self.login_as_admin()
        
        with self.app.app_context():
            product = Product(
                name='Ledger Product',
                category='cuplock',
                cuplock_type='ledger',
                product_type='scaffolding',
                price=200.0,
                is_active=True
            )
            db.session.add(product)
            db.session.commit()
            product_id = product.id
        
        response = self.client.post(f'/cuplock/admin/ledger/{product_id}/size/add', data={
            'size_label': '1m',
            'weight_kg': '4.0',
            'buy_price': '150',
            'rent_price': '15',
            'deposit_amount': '600'
        })
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        with self.app.app_context():
            size = CuplockLedgerSize.query.filter_by(
                product_id=product_id,
                size_label='1m'
            ).first()
            self.assertIsNotNone(size)
        
        print("✓ TEST PASSED: Add ledger size")
    
    # =========================================
    # TEST CASE 6: Customer-Facing Pages
    # =========================================
    def test_vertical_product_page(self):
        """Test: Load vertical product customer page"""
        with self.app.app_context():
            product = Product(
                name='Display Vertical',
                category='cuplock',
                cuplock_type='vertical',
                product_type='scaffolding',
                price=100.0,
                image_url='test.jpg',
                is_active=True
            )
            db.session.add(product)
            db.session.commit()
            product_id = product.id
        
        response = self.client.get(f'/cuplock/product/vertical/{product_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Display Vertical', response.data)
        
        print("✓ TEST PASSED: Vertical product page loads")
    
    def test_ledger_product_page(self):
        """Test: Load ledger product customer page"""
        with self.app.app_context():
            product = Product(
                name='Display Ledger',
                category='cuplock',
                cuplock_type='ledger',
                product_type='scaffolding',
                price=200.0,
                image_url='test.jpg',
                is_active=True
            )
            db.session.add(product)
            db.session.commit()
            product_id = product.id
        
        response = self.client.get(f'/cuplock/product/ledger/{product_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Display Ledger', response.data)
        
        print("✓ TEST PASSED: Ledger product page loads")
    
    # =========================================
    # TEST CASE 7: Authentication
    # =========================================
    def test_non_admin_cannot_access_admin_routes(self):
        """Test: Non-admin cannot access admin routes"""
        # Try to access without admin session
        response = self.client.get('/cuplock/admin/vertical')
        # Should redirect due to missing admin session
        self.assertIn(response.status_code, [302, 404])
        
        print("✓ TEST PASSED: Non-admin cannot access admin routes")
    
    # =========================================
    # TEST CASE 8: Edge Cases
    # =========================================
    def test_invalid_product_id(self):
        """Test: Access non-existent product"""
        response = self.client.get('/cuplock/product/vertical/99999')
        self.assertEqual(response.status_code, 404)
        
        print("✓ TEST PASSED: Invalid product ID returns 404")
    
    def test_duplicate_size(self):
        """Test: Adding duplicate size should fail"""
        self.login_as_admin()
        
        with self.app.app_context():
            product = Product(
                name='Product',
                category='cuplock',
                cuplock_type='vertical',
                product_type='scaffolding',
                price=100.0,
                is_active=True
            )
            db.session.add(product)
            db.session.commit()
            product_id = product.id
            
            # Add first size
            size1 = CuplockVerticalSize(
                product_id=product_id,
                size_label='1m',
                weight=2.5,
                buy_price=100,
                rent_price=10,
                deposit=500,
                is_active=True
            )
            db.session.add(size1)
            db.session.commit()
        
        # Try to add duplicate
        response = self.client.post(f'/cuplock/admin/vertical/{product_id}/size/add', data={
            'size_label': '1m',
            'weight': '2.5',
            'buy_price': '100',
            'rent_price': '10',
            'deposit': '500'
        })
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        
        print("✓ TEST PASSED: Duplicate size rejected")


# =========================================
# TEST SUMMARY FUNCTION
# =========================================
def run_all_tests():
    """Run all tests and print summary"""
    print("\n" + "="*70)
    print("CUPLOCK ROUTES TEST SUITE")
    print("="*70 + "\n")
    
    suite = unittest.TestLoader().loadTestsFromTestCase(CuplockRoutesTestCase)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✓ ALL TESTS PASSED!")
    else:
        print("\n✗ SOME TESTS FAILED")
    
    print("="*70 + "\n")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
