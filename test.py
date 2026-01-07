import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

db_user = os.environ.get('DB_USER')
db_password = os.environ.get('DB_PASSWORD')
db_host = os.environ.get('DB_HOST')
db_port = os.environ.get('DB_PORT')
db_name = os.environ.get('DB_NAME')

connection_string = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

try:
    engine = create_engine(connection_string)
    with engine.connect() as connection:
        
        # -------------------------------------------------------
        # 1. Print which Database we are actually connected to
        # -------------------------------------------------------
        print(f"\n🔌 Connected to DATABASE NAME: '{db_name}'")
        
        # -------------------------------------------------------
        # 2. List ALL tables in this specific database
        # -------------------------------------------------------
        print("\n📋 Searching for tables in this database...")
        query = text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        result = connection.execute(query)
        
        tables = result.fetchall()
        
        if not tables:
            print("⚠️  This database is completely EMPTY (No tables found).")
        else:
            print("✅ Tables found:")
            for table in tables:
                print(f"   - {table[0]}")

        # -------------------------------------------------------
        # 3. Check for specific common names
        # -------------------------------------------------------
        table_names = [t[0] for t in tables]
        if 'product' in table_names:
            print("\nℹ️  Table 'product' (Singular) EXISTS.")
        elif 'products' in table_names:
            print("\n❗ Found table 'products' (Plural) but code looks for 'product' (Singular).")
        else:
            print("\n❌ Neither 'product' nor 'products' found in this database.")

except Exception as e:
    print(f"\n❌ Error: {e}")