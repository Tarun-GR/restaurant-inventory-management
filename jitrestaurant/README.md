# JIT Restaurant Management System

A modern restaurant management system built with Flask and MySQL.

## Prerequisites

- Python 3.8 or higher
- MySQL 8.0 or higher
- pip (Python package installer)

## Setup Instructions

1. Clone the repository:
```bash
git clone <repository-url>
cd jitrestaurant
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Unix or MacOS:
source venv/bin/activate
```

3. Install the required packages:
```bash
pip install flask mysql-connector-python
```

4. Configure the database:
- Open `config.py` and update the MySQL connection details:
```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'database': 'restaurant_ai',
    'user': 'your_username',
    'password': 'your_password'
}
```

5. Initialize the database:
```bash
python init_db.py
```

## Running the Application

1. Start the Flask application:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

3. Login with your credentials or sign up for a new account.

## Features

- User Authentication (Login/Signup)
- Dashboard with Restaurant Overview
- Menu Management
- Inventory Tracking
- Order Management
- Sales Analytics
- Interactive Chatbot Assistant

## Project Structure

- `app.py` - Main Flask application
- `config.py` - Configuration settings
- `database.py` - Database operations
- `init_db.py` - Database initialization
- `templates/` - HTML templates
- `static/` - Static files (CSS, JS, images)

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request 