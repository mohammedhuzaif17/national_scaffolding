import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
db_host = os.environ.get('DB_HOST', 'localhost')
db_port = os.environ.get('DB_PORT', '5432')
db_user = os.environ.get('DB_USER', 'postgres')
db_password = os.environ.get('DB_PASSWORD', 'postgres')
db_name = os.environ.get('DB_NAME', 'national_scaffolding')

def setup_database():
    try:
        # Connect to PostgreSQL server (without specifying a database)
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database='postgres'  # Connect to default postgres database
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
            cursor.execute(
                sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier(db_name)
                )
            )
            print(f"Database '{db_name}' created successfully.")
        else:
            print(f"Database '{db_name}' already exists.")
        
        # Close connection to postgres database
        cursor.close()
        conn.close()
        
        # Connect to the newly created database
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Create extensions if needed
        try:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
            print("UUID extension created successfully.")
        except Exception as e:
            print(f"Error creating UUID extension: {e}")
        
        print(f"Database setup for '{db_name}' completed successfully.")
        
        # Close connection
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        print(f"Error setting up database: {e}")
        return False

if __name__ == "__main__":
    setup_database()