"""
Complete Database Setup and Schema for National Scaffolding Platform
This script handles database creation and table initialization with all Cuplock models
"""

import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Database connection parameters
db_host = os.environ.get('DB_HOST', 'localhost')
db_port = os.environ.get('DB_PORT', '5432')
db_user = os.environ.get('DB_USER', 'postgres')
db_password = os.environ.get('DB_PASSWORD', 'postgres')
db_name = os.environ.get('DB_NAME', 'national_scaffolding')


def execute_sql(cursor, sql_query, description=""):
    """Execute SQL query with error handling"""
    try:
        cursor.execute(sql_query)
        if description:
            print(f"✓ {description}")
        return True
    except Exception as e:
        print(f"✗ Error {description}: {e}")
        return False


def setup_database():
    """Create database if it doesn't exist"""
    try:
        # Connect to PostgreSQL server (without specifying a database)
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database='postgres'
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(
            sql.SQL("SELECT 1 FROM pg_database WHERE datname = {}").format(
                sql.Literal(db_name)
            )
        )
        exists = cursor.fetchone()
        
        # Create database if it doesn't exist
        if not exists:
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
            print(f"✓ Database '{db_name}' created successfully")
        else:
            print(f"✓ Database '{db_name}' already exists")
        
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        print(f"✗ Error setting up database: {e}")
        return False


def create_tables():
    """Create all required database tables"""
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("\n=== Creating Tables ===\n")
        
        # Enable UUID extension
        execute_sql(cursor, 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp"', "UUID extension")
        
        # Create users table
        execute_sql(cursor, """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL,
                full_name VARCHAR(200) NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                phone VARCHAR(20) UNIQUE NOT NULL,
                address TEXT,
                organization VARCHAR(200),
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """, "users table")
        
        # Create indexes for users
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)", "idx_users_email")
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone)", "idx_users_phone")
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)", "idx_users_username")
        
        # Create admins table
        execute_sql(cursor, """
            CREATE TABLE IF NOT EXISTS admins (
                id SERIAL PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                panel_type VARCHAR(50) NOT NULL
            )
        """, "admins table")
        
        # Create indexes for admins
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_admins_username ON admins(username)", "idx_admins_username")
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_admins_panel_type ON admins(panel_type)", "idx_admins_panel_type")
        
        # Create products table
        execute_sql(cursor, """
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                description TEXT,
                category VARCHAR(100),
                product_type VARCHAR(50) NOT NULL,
                customization_options JSONB,
                rent_price DECIMAL(10,2),
                deposit_amount DECIMAL(10,2),
                image_url VARCHAR(500),
                weight_per_unit DECIMAL(10,2),
                cuplock_type VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """, "products table")
        
        # Create indexes for products
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category)", "idx_products_category")
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_products_type ON products(product_type)", "idx_products_type")
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_products_name ON products(name)", "idx_products_name")
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_products_cuplock_type ON products(cuplock_type)", "idx_products_cuplock_type")
        
        # Create cuplock_vertical_size table
        execute_sql(cursor, """
            CREATE TABLE IF NOT EXISTS cuplock_vertical_size (
                id SERIAL PRIMARY KEY,
                product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                size_label VARCHAR(50) NOT NULL,
                display_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(product_id, size_label)
            )
        """, "cuplock_vertical_size table")
        
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_cuplock_vertical_size_product_id ON cuplock_vertical_size(product_id)", "idx_cuplock_vertical_size_product_id")
        
        # Create cuplock_vertical_cup table
        execute_sql(cursor, """
            CREATE TABLE IF NOT EXISTS cuplock_vertical_cup (
                id SERIAL PRIMARY KEY,
                vertical_size_id INTEGER NOT NULL REFERENCES cuplock_vertical_size(id) ON DELETE CASCADE,
                cup_count INTEGER NOT NULL,
                cup_image_url VARCHAR(255),
                weight_kg DECIMAL(10,2),
                buy_price DECIMAL(10,2) NOT NULL,
                rent_price DECIMAL(10,2) NOT NULL,
                deposit_amount DECIMAL(10,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(vertical_size_id, cup_count)
            )
        """, "cuplock_vertical_cup table")
        
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_cuplock_vertical_cup_vertical_size_id ON cuplock_vertical_cup(vertical_size_id)", "idx_cuplock_vertical_cup_vertical_size_id")
        
        # Create cuplock_ledger_size table
        execute_sql(cursor, """
            CREATE TABLE IF NOT EXISTS cuplock_ledger_size (
                id SERIAL PRIMARY KEY,
                product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                size_label VARCHAR(100) NOT NULL,
                weight_kg DECIMAL(10,2) NOT NULL,
                buy_price DECIMAL(10,2) NOT NULL,
                rent_price DECIMAL(10,2) NOT NULL,
                deposit_amount DECIMAL(10,2),
                display_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(product_id, size_label)
            )
        """, "cuplock_ledger_size table")
        
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_cuplock_ledger_size_product_id ON cuplock_ledger_size(product_id)", "idx_cuplock_ledger_size_product_id")
        
        # Create legacy cuplock_vertical_options table (backward compatibility)
        execute_sql(cursor, """
            CREATE TABLE IF NOT EXISTS cuplock_vertical_options (
                id SERIAL PRIMARY KEY,
                product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
                size VARCHAR(10) NOT NULL,
                cups_configuration VARCHAR(20) NOT NULL,
                weight DECIMAL(5,2),
                buy_price DECIMAL(10,2),
                rent_price DECIMAL(10,2),
                UNIQUE(product_id, size, cups_configuration)
            )
        """, "cuplock_vertical_options table (legacy)")
        
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_cuplock_vertical_product_id ON cuplock_vertical_options(product_id)", "idx_cuplock_vertical_product_id")
        
        # Create legacy cuplock_ledger_options table (backward compatibility)
        execute_sql(cursor, """
            CREATE TABLE IF NOT EXISTS cuplock_ledger_options (
                id SERIAL PRIMARY KEY,
                product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
                size VARCHAR(10) NOT NULL,
                weight DECIMAL(5,2),
                buy_price DECIMAL(10,2),
                rent_price DECIMAL(10,2),
                UNIQUE(product_id, size)
            )
        """, "cuplock_ledger_options table (legacy)")
        
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_cuplock_ledger_product_id ON cuplock_ledger_options(product_id)", "idx_cuplock_ledger_product_id")
        
        # Create orders table
        execute_sql(cursor, """
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                total_price DECIMAL(10,2) NOT NULL,
                order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(50) DEFAULT 'pending_verification',
                transaction_id VARCHAR(255) UNIQUE NOT NULL,
                amount_paid DECIMAL(10,2),
                payment_time TIMESTAMP
            )
        """, "orders table")
        
        # Create indexes for orders
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id)", "idx_orders_user_id")
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)", "idx_orders_status")
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_orders_transaction_id ON orders(transaction_id)", "idx_orders_transaction_id")
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date)", "idx_orders_date")
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_orders_payment_time ON orders(payment_time)", "idx_orders_payment_time")
        
        # Create order_items table
        execute_sql(cursor, """
            CREATE TABLE IF NOT EXISTS order_items (
                id SERIAL PRIMARY KEY,
                order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                product_name VARCHAR(200) NOT NULL,
                quantity INTEGER NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                customization JSONB
            )
        """, "order_items table")
        
        # Create indexes for order_items
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id)", "idx_order_items_order_id")
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id)", "idx_order_items_product_id")
        
        print("\n✓ All tables created successfully\n")
        
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        print(f"\n✗ Error creating tables: {e}\n")
        return False


def insert_default_data():
    """Insert default admin users and sample products"""
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("=== Inserting Default Data ===\n")
        
        # Insert default admin users
        cursor.execute("""
            INSERT INTO admins (username, password_hash, panel_type) 
            VALUES 
                ('admin_scaffolding', 'pbkdf2:sha256:260000$8gNzZ7Q8r7K8L7mW$7d9c8f8e8d8c8b8a89888786858483828180', 'scaffolding'),
                ('admin_fabrication', 'pbkdf2:sha256:260000$9hO0a8R9s8L8mW$8e9d9f9e9d9c9b9a99989796959493929190', 'fabrication')
            ON CONFLICT (username) DO NOTHING
        """)
        print("✓ Default admin users inserted")
        
        # Insert sample products
        products_data = [
            # Scaffolding Products
            ('Aluminium Scaffolding 6x4', 1200.00, 'Standard aluminium scaffolding 6ft x 4ft', 'aluminium', 'scaffolding', 240.00, 300.00, 15.00),
            ('Aluminium Scaffolding 8x6', 1700.00, 'Large aluminium scaffolding 8ft x 6ft', 'aluminium', 'scaffolding', 340.00, 400.00, 18.00),
            ('H-Frame Scaffolding', 500.00, 'Durable H-frame scaffolding system', 'h-frames', 'scaffolding', 100.00, 150.00, 10.00),
            ('Cuplock Scaffolding - Vertical', 390.00, 'Versatile vertical cuplock scaffolding system', 'cuplock', 'scaffolding', None, None, 5.00),
            ('Cuplock Scaffolding - Ledger', 350.00, 'Versatile ledger cuplock scaffolding system', 'cuplock', 'scaffolding', None, None, 4.00),
            ('Scaffolding Base Jack', 50.00, 'Adjustable base jack for level adjustment', 'accessories', 'scaffolding', 10.00, 20.00, 2.00),
            ('Scaffolding Coupler', 25.00, 'Heavy-duty scaffolding coupler', 'accessories', 'scaffolding', 5.00, 10.00, 1.00),
            
            # Fabrication Products
            ('Steel Beam Fabrication', 2000.00, 'Custom steel beam fabrication service', 'steel', 'fabrication', None, None, 25.00),
            ('Aluminium Window Frame', 1500.00, 'Custom aluminium window frame fabrication', 'aluminium', 'fabrication', None, None, 8.00),
            ('Metal Staircase Fabrication', 5000.00, 'Complete metal staircase fabrication', 'steel', 'fabrication', None, None, 150.00),
            ('Custom Metal Grating', 800.00, 'Industrial metal grating fabrication', 'steel', 'fabrication', None, None, 30.00)
        ]
        
        for name, price, desc, category, ptype, rent, deposit, weight in products_data:
            cuplock_t = None
            if 'Vertical' in name:
                cuplock_t = 'vertical'
            elif 'Ledger' in name:
                cuplock_t = 'ledger'
            
            cursor.execute("""
                INSERT INTO products (name, price, description, category, product_type, rent_price, deposit_amount, weight_per_unit, cuplock_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (name, price, desc, category, ptype, rent, deposit, weight, cuplock_t))
        
        print("✓ Sample products inserted")
        
        # Get the vertical cuplock product and insert sample configurations
        cursor.execute("SELECT id FROM products WHERE name = 'Cuplock Scaffolding - Vertical' LIMIT 1")
        vertical_product = cursor.fetchone()
        
        if vertical_product:
            product_id = vertical_product[0]
            
            # Check if already configured
            cursor.execute("SELECT COUNT(*) FROM cuplock_vertical_size WHERE product_id = %s", (product_id,))
            if cursor.fetchone()[0] == 0:
                # Insert sample vertical sizes
                vertical_sizes = [
                    ('0.9m', 0),
                    ('1.0m', 1),
                    ('1.5m', 2),
                    ('2.0m', 3),
                ]
                
                for size_label, order in vertical_sizes:
                    cursor.execute("""
                        INSERT INTO cuplock_vertical_size (product_id, size_label, display_order)
                        VALUES (%s, %s, %s)
                        RETURNING id
                    """, (product_id, size_label, order))
                    
                    size_id = cursor.fetchone()[0]
                    
                    # Insert cups for each size
                    cups_for_size = {
                        '0.9m': [(1, 4.5, 150, 15, 40), (2, 5.2, 180, 18, 50)],
                        '1.0m': [(1, 4.8, 160, 16, 45), (2, 5.8, 190, 19, 55), (3, 6.5, 220, 22, 65)],
                        '1.5m': [(2, 6.2, 200, 20, 55), (3, 7.0, 240, 24, 70), (4, 7.8, 280, 28, 85)],
                        '2.0m': [(2, 7.2, 220, 22, 65), (3, 8.0, 260, 26, 80), (4, 8.8, 300, 30, 95)]
                    }
                    
                    for cup_count, weight, buy, rent, deposit in cups_for_size[size_label]:
                        cursor.execute("""
                            INSERT INTO cuplock_vertical_cup (vertical_size_id, cup_count, weight_kg, buy_price, rent_price, deposit_amount)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT DO NOTHING
                        """, (size_id, cup_count, weight, buy, rent, deposit))
                
                print("✓ Sample cuplock vertical configurations inserted")
        
        # Get the ledger cuplock product and insert sample configurations
        cursor.execute("SELECT id FROM products WHERE name = 'Cuplock Scaffolding - Ledger' LIMIT 1")
        ledger_product = cursor.fetchone()
        
        if ledger_product:
            product_id = ledger_product[0]
            
            # Check if already configured
            cursor.execute("SELECT COUNT(*) FROM cuplock_ledger_size WHERE product_id = %s", (product_id,))
            if cursor.fetchone()[0] == 0:
                # Insert sample ledger sizes
                ledger_sizes = [
                    ('0.9m', 3.5, 200, 20, 50, 0),
                    ('1.2m', 4.0, 230, 23, 60, 1),
                    ('1.5m', 4.5, 260, 26, 70, 2),
                    ('2.0m', 5.5, 300, 30, 85, 3),
                    ('2.5m', 6.0, 330, 33, 95, 4),
                    ('3.0m', 6.5, 360, 36, 105, 5),
                ]
                
                for size_label, weight, buy, rent, deposit, order in ledger_sizes:
                    cursor.execute("""
                        INSERT INTO cuplock_ledger_size (product_id, size_label, weight_kg, buy_price, rent_price, deposit_amount, display_order)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """, (product_id, size_label, weight, buy, rent, deposit, order))
                
                print("✓ Sample cuplock ledger configurations inserted")
        
        print("\n✓ All default data inserted successfully\n")
        
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        print(f"\n✗ Error inserting default data: {e}\n")
        return False


def main():
    """Main function to run complete database setup"""
    print("\n" + "="*50)
    print("DATABASE SETUP - National Scaffolding Platform")
    print("="*50 + "\n")
    
    # Step 1: Setup database
    print("Step 1: Creating database...")
    if not setup_database():
        print("Failed to create database. Exiting.")
        return False
    
    # Step 2: Create tables
    print("\nStep 2: Creating tables...")
    if not create_tables():
        print("Failed to create tables. Exiting.")
        return False
    
    # Step 3: Insert default data
    print("Step 3: Inserting default data...")
    if not insert_default_data():
        print("Failed to insert default data. Exiting.")
        return False
    
    print("="*50)
    print("DATABASE SETUP COMPLETE!")
    print("="*50 + "\n")
    
    print("✓ Database and all tables ready")
    print("✓ Default admin users created")
    print("✓ Sample products inserted")
    print("✓ Cuplock configurations configured\n")
    
    return True


if __name__ == "__main__":
    main()