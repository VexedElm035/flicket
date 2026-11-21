#!/usr/bin/env bash
set -e

# Generate config.json if it does not exist or if FORCE_CONFIG_GEN is set
python3 - << 'EOF'
import os
import json
from base64 import b64encode

config_file = os.environ.get('FLICKET_CONFIG_FILE', 'config.json')

def random_string(bytes_=24):
    return b64encode(os.urandom(bytes_)).decode('utf-8')

if not os.path.exists(config_file) or os.environ.get('FORCE_CONFIG_GEN') == '1':
    print(f"Generating {config_file} from environment variables...")
    config_values = {
        'db_type': int(os.environ.get('DB_TYPE', '3')),
        'db_driver': os.environ.get('DB_DRIVER', 'pymysql'),
        'db_username': os.environ.get('DB_USER', os.environ.get('DB_USERNAME', 'flicket')),
        'db_password': os.environ.get('DB_PASSWORD', 'flicket_password'),
        'db_url': os.environ.get('DB_HOST', os.environ.get('DB_URL', 'db')),
        'db_port': os.environ.get('DB_PORT', '3306'),
        'db_name': os.environ.get('DB_NAME', 'flicket'),
        'SECRET_KEY': os.environ.get('SECRET_KEY', random_string()),
        'NOTIFICATION_USER_PASSWORD': os.environ.get('NOTIFICATION_USER_PASSWORD', random_string())
    }
    with open(config_file, 'w') as f:
        json.dump(config_values, f, indent=4)
    print(f"Generated {config_file} successfully.")
else:
    print(f"Using existing {config_file}.")
EOF

# Wait for database connection
echo "Checking database connection..."
python3 - << 'EOF'
import os
import sys
import time
import json
from sqlalchemy import create_engine

config_file = os.environ.get('FLICKET_CONFIG_FILE', 'config.json')
with open(config_file, 'r') as f:
    config_data = json.load(f)

db_type = config_data.get('db_type', 3)
if db_type == 1:
    print("Using SQLite database. No network check required.")
else:
    dialect = 'postgresql' if db_type == 2 else 'mysql'
    driver = config_data.get('db_driver') or 'pymysql'
    user = config_data['db_username']
    pwd = config_data['db_password']
    host = config_data['db_url']
    port = config_data['db_port']
    name = config_data['db_name']
    uri = f"{dialect}+{driver}://{user}:{pwd}@{host}:{port}/{name}"

    retries = 30
    while retries > 0:
        try:
            engine = create_engine(uri)
            with engine.connect():
                print("Database connection verified.")
                break
        except Exception as e:
            print(f"Waiting for database to be ready ({e}). Retrying in 2 seconds... ({retries} attempts left)")
            retries -= 1
            time.sleep(2)
    else:
        print("Error: Could not connect to database.")
        sys.exit(1)
EOF

# Run database migrations
echo "Running database migrations..."
flask --app application db upgrade

# Run initial setup / seeding
echo "Running database auto-setup..."
python3 -m scripts.docker_setup

# Execute CMD
echo "Starting Flicket application..."
exec "$@"
