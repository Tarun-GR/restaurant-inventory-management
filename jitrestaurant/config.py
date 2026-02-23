import os

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'database': 'restaurant_ai',
    'user': 'root',
    'password': 'annamalai'
}

# You can also use environment variables for security
# DB_CONFIG = {
#     'host': os.getenv('DB_HOST', 'localhost'),
#     'port': int(os.getenv('DB_PORT', 3306)),
#     'database': os.getenv('DB_NAME', 'jit_restaurant'),
#     'user': os.getenv('DB_USER', 'your_username'),
#     'password': os.getenv('DB_PASSWORD', 'your_password')
# }
