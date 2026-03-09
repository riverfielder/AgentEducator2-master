import socket
import os
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

uri = os.getenv("SQLALCHEMY_DATABASE_URI")
if not uri:
    print("Error: SQLALCHEMY_DATABASE_URI not found in .env")
    exit(1)

# Parse uri: mysql+pymysql://user:pass@host:port/dbname
try:
    # Remove the driver part to make it standard format for urlparse if needed, 
    # but urlparse handles schemes fine usually.
    # format: scheme://netloc/path
    result = urlparse(uri)
    host = result.hostname
    port = result.port or 3306
    print(f"Parsed Config: Host={host}, Port={port}")
except Exception as e:
    print(f"Error parsing URI: {e}")
    exit(1)

print(f"Testing connection to {host}:{port}...")

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(5)
try:
    s.connect((host, port))
    print("Success: Port is open and accepting connections.")
    s.close()
except Exception as e:
    print(f"Error: Could not connect. Reason: {e}")
