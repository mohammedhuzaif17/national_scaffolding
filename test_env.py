import os
from dotenv import load_dotenv

load_dotenv()

print("=== Database Settings ===")
print(f"DB_HOST: {os.environ.get('DB_HOST')}")
print(f"DB_PORT: {os.environ.get('DB_PORT')}")
print(f"DB_USER: {os.environ.get('DB_USER')}")
print(f"DB_PASSWORD: {os.environ.get('DB_PASSWORD')}")
print(f"DB_NAME: {os.environ.get('DB_NAME')}")

print("\n=== Connection String ===")
db_user = os.environ.get('DB_USER', 'postgres')
db_password = os.environ.get('DB_PASSWORD', 'postgres')
db_host = os.environ.get('DB_HOST', 'localhost')
db_port = os.environ.get('DB_PORT', '5432')
db_name = os.environ.get('DB_NAME', 'national_scaffolding')

connection_string = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
print(f"Connection: {connection_string}")