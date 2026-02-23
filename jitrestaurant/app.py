from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import mysql.connector
import os
import logging
from datetime import datetime, timedelta
from functools import wraps
from database import (
    fetch_all_dishes, fetch_ingredients, fetch_inventory,
    fetch_batches, fetch_suppliers, fetch_customers,
    fetch_orders, fetch_sales, fetch_login_history,
    fetch_inventory_with_usage, fetch_recent_orders,
    get_db_connection, log_logout, log_user_activity,
    verify_admin_login, verify_staff_login, log_login
)
import hashlib
from config import DB_CONFIG

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

app = Flask(__name__)
# Use a fixed secret key instead of a random one
app.secret_key = 'your-fixed-secret-key-123'  # Replace with your own secret key
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=60)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User class for Flask-Login with is_admin property
class User(UserMixin):
    def __init__(self, id, username, email, is_admin=False):
        self.id = id
        self.username = username
        self.email = email
        self.is_admin = is_admin

@login_manager.user_loader
def load_user(user_id):
    if user_id == '0':  # Special case for admin
        admin_user = User(id=0, username='admin', email='admin@jitrestaurant.com', is_admin=True)
        return admin_user
        
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if user:
            return User(user['id'], user['username'], user['email'])
    except mysql.connector.Error as err:
        logger.error(f"Error loading user: {err}")
    finally:
        conn.close()
    return None

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['pswd']
        hashed_password = hash_password(password)
        ip_address = request.remote_addr

        conn = get_db_connection()
        if not conn:
            flash('Unable to connect to database', 'error')
            return redirect(url_for('login'))

        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", 
                         (email, hashed_password))
            user = cursor.fetchone()
            
            if user:
                user_obj = User(user['id'], user['username'], user['email'])
                login_user(user_obj)
                
                # Log the successful login
                login_id = log_login(user['id'], user['username'], 'user', ip_address)
                session['login_id'] = login_id
                
                # Log the activity
                log_user_activity(
                    user['id'], 
                    user['username'], 
                    'user', 
                    'Login', 
                    'Login successful',
                    ip_address
                )
                
                flash('Welcome back!', 'success')
                return redirect(url_for('dashboard'))
            
            # Log failed login attempt
            log_user_activity(
                None, 
                email, 
                'user', 
                'Login Failed', 
                'Invalid credentials',
                ip_address,
                'failed'
            )
            
            flash('Invalid email or password', 'error')
            return redirect(url_for('login'))
                
        except mysql.connector.Error as err:
            logger.error(f"Login DB error: {err}")
            flash('An error occurred during login. Please try again.', 'error')
        finally:
            if conn and conn.is_connected():
                conn.close()
                logger.debug("Database connection closed")
                
    return render_template('login.html')

@app.route('/restaurant_login', methods=['GET', 'POST'])
def restaurant_login():
    return render_template('restaurant_login.html')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Please login as admin to access this page.', 'error')
            return redirect(url_for('restaurant_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin_landing')
@admin_required
def admin_landing():
    try:
        logger.debug("Starting to fetch data for admin landing page")
        
        # Fetch all required data
        logger.debug("Fetching customer orders...")
        customer_orders = fetch_orders()
        logger.debug(f"Customer orders data: {customer_orders}")
        
        logger.debug("Fetching inventory batches...")
        inventory_batches = fetch_batches()
        logger.debug(f"Inventory batches count: {len(inventory_batches)}")
        
        logger.debug("Fetching inventory items...")
        inventory_items = fetch_inventory()
        logger.debug(f"Inventory items count: {len(inventory_items)}")
        
        logger.debug("Fetching sales data...")
        sales = fetch_sales()
        logger.debug(f"Sales data count: {len(sales)}")
        
        logger.debug("Fetching suppliers...")
        suppliers = fetch_suppliers()
        logger.debug(f"Suppliers count: {len(suppliers)}")
        
        logger.debug("Fetching order details...")
        order_details = fetch_recent_orders()
        logger.debug(f"Order details data: {order_details}")

        return render_template('admin_landing.html',
                           admin_name=current_user.username,
                           customer_orders=customer_orders,
                           inventory_batches=inventory_batches,
                           inventory_items=inventory_items,
                           sales=sales,
                           suppliers=suppliers,
                           order_details=order_details)
    except Exception as e:
        logger.error(f"Admin landing error: {str(e)}")
        flash(str(e), 'error')
        return render_template('admin_landing.html', error=str(e))

@app.route('/admin_login', methods=['POST'])
def admin_login():
    username = request.form['username']
    password = request.form['password']
    ip_address = request.remote_addr

    # Fixed admin credentials
    if username == 'admin' and password == 'admin123':
        # Create a User object for the admin with is_admin=True
        admin_user = User(id=0, username='admin', email='admin@jitrestaurant.com', is_admin=True)
        login_user(admin_user)
        session.permanent = True  # Make the session permanent
        
        # Log the successful login
        login_id = log_login(None, username, 'admin', ip_address)
        session['login_id'] = login_id
        
        # Log the activity
        log_user_activity(
            None, 
            username, 
            'admin', 
            'Login', 
            'Admin login successful',
            ip_address
        )
        
        flash('Welcome back, Admin!', 'success')
        return redirect(url_for('admin_landing'))
    
    # Log failed login attempt
    log_user_activity(
        None, 
        username, 
        'admin', 
        'Login Failed', 
        'Invalid admin credentials',
        ip_address,
        'failed'
    )
    
    flash('Invalid admin credentials', 'error')
    return redirect(url_for('restaurant_login'))

def staff_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.is_admin:
            flash('Please login as staff to access this page.', 'error')
            return redirect(url_for('restaurant_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/staff_landing')
@staff_required
def staff_landing():
    try:
        logger.debug("Starting to fetch data for staff landing page")
        
        # Initialize data with default values
        data = {
            'staff_name': current_user.username if current_user else None,
            'customer_orders': [],
            'dishes': [],
            'order_details': [],
            'error': None
        }
        
        # Fetch required data
        customer_orders = fetch_orders()
        logger.debug(f"Customer orders data: {customer_orders}")
        if customer_orders:
            data['customer_orders'] = customer_orders
        
        dishes = fetch_all_dishes()
        logger.debug(f"Dishes data: {len(dishes)} records")
        if dishes:
            data['dishes'] = dishes
        
        order_details = fetch_recent_orders()
        logger.debug(f"Order details data: {order_details}")
        if order_details:
            data['order_details'] = order_details

        logger.debug(f"Rendering staff_landing.html with data: {data}")
        return render_template('staff_landing.html', **data)
    except Exception as e:
        logger.error(f"Staff landing error: {str(e)}")
        return render_template('staff_landing.html', 
                             staff_name=current_user.username if current_user else None,
                             customer_orders=[],
                             dishes=[],
                             order_details=[],
                             error=str(e))

@app.route('/staff_login', methods=['POST'])
def staff_login():
    username = request.form['username']
    password = request.form['password']
    ip_address = request.remote_addr

    # Fixed staff credentials
    if username == 'staff' and password == 'staff123':
        # Create a User object for the staff
        staff_user = User(id=1, username='staff', email='staff@jitrestaurant.com', is_admin=False)
        login_user(staff_user)
        session.permanent = True
        
        # Log the successful login
        login_id = log_login(1, username, 'staff', ip_address)
        session['login_id'] = login_id
        
        # Log the activity
        log_user_activity(
            1, 
            username, 
            'staff', 
            'Login', 
            'Staff login successful',
            ip_address
        )
        
        flash('Welcome back!', 'success')
        return redirect(url_for('staff_landing'))
    
    # Log failed login attempt
    log_user_activity(
        None, 
        username, 
        'staff', 
        'Login Failed', 
        'Invalid staff credentials',
        ip_address,
        'failed'
    )
    
    flash('Invalid staff credentials', 'error')
    return redirect(url_for('restaurant_login'))

@app.route('/signup', methods=['POST'])
def signup():
    try:
        username = request.form['txt']
        email = request.form['email']
        phone = request.form['broj']
        password = request.form['pswd']
        
        logger.debug(f"Signup attempt - Username: {username}, Email: {email}, Phone: {phone}")

        # Validate required fields
        if not all([username, email, phone, password]):
            logger.debug("Missing required fields")
            flash('All fields are required.', 'error')
            return redirect(url_for('login'))

        if len(password) < 6:
            logger.debug("Password too short")
            flash('Password must be at least 6 characters long.', 'error')
            return redirect(url_for('login'))

        # Validate email format
        if '@' not in email or '.' not in email:
            logger.debug("Invalid email format")
            flash('Please enter a valid email address.', 'error')
            return redirect(url_for('login'))

        # Validate phone number (10 digits)
        if not phone.isdigit() or len(phone) != 10:
            logger.debug("Invalid phone number format")
            flash('Please enter a valid 10-digit phone number.', 'error')
            return redirect(url_for('login'))
        
        hashed_password = hash_password(password)
        logger.debug("Password hashed successfully")

        # Try to connect to database
        conn = None
        try:
            conn = get_db_connection()
            if not conn:
                logger.error("Failed to establish database connection")
                flash('Database connection failed. Please try again later.', 'error')
                return redirect(url_for('login'))

            cursor = conn.cursor()
            logger.debug("Checking for existing user...")
            
            # Check if username or email already exists
            cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
            existing_user = cursor.fetchone()
            
            if existing_user:
                logger.debug(f"User already exists: {existing_user}")
                if existing_user[1] == username:
                    flash('Username already exists. Please choose a different username.', 'error')
                else:
                    flash('Email already registered. Please use a different email or login.', 'error')
                return redirect(url_for('login'))

            logger.debug("Inserting new user...")
            # Insert new user
            cursor.execute("""
                INSERT INTO users (username, email, phone_number, password)
                VALUES (%s, %s, %s, %s)
            """, (username, email, phone, hashed_password))
            
            conn.commit()
            logger.info(f"New user registered successfully: {username}")
            flash('Account created successfully! Please login.', 'success')
            return redirect(url_for('login'))
            
        except mysql.connector.Error as err:
            logger.error(f"Database error during signup: {err}")
            logger.error(f"Error code: {err.errno}")
            logger.error(f"SQL state: {err.sqlstate}")
            logger.error(f"Error message: {err.msg}")
            
            if conn:
                conn.rollback()
            
            if err.errno == 1062:  # Duplicate entry error
                flash('Username or email already exists. Please try again.', 'error')
            elif err.errno == 1045:  # Access denied
                flash('Database access error. Please contact support.', 'error')
            elif err.errno == 2003:  # Can't connect to server
                flash('Unable to connect to database. Please try again later.', 'error')
            else:
                flash(f'Database error: {err.msg}', 'error')
            return redirect(url_for('login'))
                
    except Exception as e:
        logger.error(f"Unexpected error during signup: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        flash('An unexpected error occurred. Please try again.', 'error')
        return redirect(url_for('login'))
    
    finally:
        if conn and conn.is_connected():
            conn.close()
            logger.debug("Database connection closed")

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        dishes = fetch_all_dishes()
        inventory = fetch_inventory()
        orders = fetch_orders()
        sales = fetch_sales()

        data = {
            'user': current_user,
            'dishes': dishes,
            'inventory': inventory,
            'orders': orders,
            'sales': sales
        }
        return render_template('dashboard.html', **data)
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        flash(str(e), 'error')
        return render_template('dashboard.html', error=str(e), user=current_user)

@app.route('/contact', methods=['POST'])
@login_required
def contact():
    flash("Thank you! We'll get back to you soon.", 'success')
    return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout():
    try:
        if current_user.is_authenticated:
            # Get user info before logout
            user_id = current_user.id
            username = current_user.username
            is_admin = current_user.is_admin
            
            # Log the logout in LoginHistory
            login_id = session.get('login_id')
            if login_id:
                log_logout(login_id)
            
            # Log the activity
            log_user_activity(
                user_id,
                username,
                'user',
                'Logout',
                'User logged out successfully',
                request.remote_addr
            )
            
            # Clear all session data
            session.clear()
            
            # Logout the user
            logout_user()
            
            flash('You have been logged out successfully.', 'success')
            
            # Check if the request came from admin/staff landing
            referrer = request.referrer
            if referrer and ('staff_landing' in referrer or 'admin_landing' in referrer):
                return redirect(url_for('restaurant_login'))
            else:
                return redirect(url_for('login'))
            
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        flash('An error occurred during logout.', 'error')
        return redirect(url_for('login'))

@app.route('/menu')
@login_required
def menu():
    try:
        dishes = fetch_all_dishes()
        ingredients = fetch_ingredients()
        data = {
            'user': current_user,
            'dishes': dishes,
            'ingredients': ingredients
        }
        return render_template('menu.html', **data)
    except Exception as e:
        logger.error(f"Menu route error: {str(e)}")
        flash(str(e), 'error')
        return render_template('menu.html', error=str(e), user=current_user)

@app.route('/inventory')
@login_required
def inventory():
    try:
        data = {
            'user': current_user,
            'inventory': fetch_inventory(),
            'batches': fetch_batches(),
            'suppliers': fetch_suppliers()
        }
        return render_template('inventory.html', **data)
    except Exception as e:
        logger.error(f"Inventory error: {str(e)}")
        flash(str(e), 'error')
        return render_template('inventory.html', error=str(e), user=current_user)

@app.route('/orders')
@login_required
def orders():
    try:
        data = {
            'user': current_user,
            'orders': fetch_orders(),
            'sales': fetch_sales()
        }
        return render_template('orders.html', **data)
    except Exception as e:
        logger.error(f"Orders error: {str(e)}")
        flash(str(e), 'error')
        return render_template('orders.html', error=str(e), user=current_user)

@app.route('/chatbot', methods=['POST'])
@login_required
def chatbot():
    try:
        data = request.get_json()
        user_message = data.get('message', '').lower()

        # Expanded and flexible chatbot responses
        responses = {
            # Menu & Dishes
            'menu': "Our menu features a variety of dishes including vegetarian, vegan, and gluten-free options. Ask for today's specials or any dish details!",
            'specials': "Today's specials are Butter Chicken, Paneer Tikka, and Garlic Naan. Would you like to know more?",
            'ingredients': "You can view ingredients for any dish by asking, e.g., 'What are the ingredients in Veg Biryani?'",
            'recommend': "I recommend our Chef's Special: Masala Dosa with Coconut Chutney!",
            'dish': "Ask about any dish for details, price, or ingredients.",

            # Inventory
            'inventory': "You can check current stock, add new items, or get low stock alerts. Ask 'What's low in stock?' or 'Add new batch'.",
            'stock': "To check stock levels, go to the Inventory section. Low stock items are highlighted for your convenience.",
            'supplier': "To add a new supplier, go to the Inventory page and click 'New Supplier'. You can also view supplier contact info here.",
            'batch': "Add a new inventory batch from the Inventory Batches section. Enter item, quantity, and expiry date.",

            # Orders
            'order': "To place an order, add items to your cart and proceed to checkout. You can track order status in the Orders section.",
            'order status': "Order statuses include: Pending, Preparing, Ready, Served, and Cancelled. Ask for a specific order's status by order ID.",
            'cancel order': "To cancel an order, go to Orders, select the order, and click 'Cancel'.",
            'track order': "Track your order in the Orders section. You'll see real-time status updates.",
            'recent orders': "View recent orders in the Orders section. You can also see order details and status.",

            # Sales & Analytics
            'sales': "View daily, weekly, or monthly sales analytics in the Sales section. Ask for 'today's sales' or 'top selling dishes'.",
            'analytics': "Sales analytics include revenue, bestsellers, and trends. Go to the Sales section for details.",
            'revenue': "Revenue reports are available in the Sales section. You can filter by date or dish.",

            # Staff
            'staff': "Staff can log in, view schedules, and manage orders. Admins can add or remove staff from the Admin panel.",
            'staff login': "Staff can log in from the Restaurant Login page using their credentials.",
            'staff schedule': "Staff schedules are managed by the admin. Contact your manager for details.",

            # Customers
            'customer': "Customers can place orders, give feedback, and join our loyalty program. Ask about 'customer rewards' or 'feedback'.",
            'feedback': "We value customer feedback! Use the Contact section or ask staff for a feedback form.",
            'loyalty': "Our loyalty program rewards frequent customers. Ask about your points or rewards at checkout.",

            # Admin
            'admin': "Admins can manage users, view reports, and adjust system settings. For help, type 'admin help'.",
            'user management': "Admins can add, edit, or remove users from the Admin panel.",
            'settings': "System settings are available to admins in the Admin panel.",
            'report': "Generate sales, inventory, and staff reports from the Admin panel.",

            # General Info
            'hours': "We are open from 10am to 11pm, 7 days a week.",
            'timings': "Our restaurant operates daily from 10am to 11pm.",
            'address': "We are located at #42, Whitefield Tech Park, Bangalore.",
            'location': "Find us at #42, Whitefield Tech Park, ITPL Main Road, Bangalore.",
            'contact': "Contact us at contact@jitrestaurant.com or +91 80 4567 8900.",
            'phone': "You can reach us at +91 80 4567 8900.",
            'email': "Email us at contact@jitrestaurant.com for any queries.",
            'events': "We host special events and offers. Check our website or ask for upcoming events!",
            'policy': "For our restaurant policies, please ask about a specific topic (e.g., refund, reservation, etc.).",

            # Troubleshooting
            'login problem': "If you're having trouble logging in, try resetting your password or contact support.",
            'order error': "If you encounter an order error, please refresh the page or contact admin.",
            'payment': "For payment issues, ensure your details are correct or contact support.",
            'support': "For any issues, contact our support team at support@jitrestaurant.com.",

            # AI Assistant
            'help': "I can help you with menu, orders, inventory, sales, staff, and more. Just type your question!",
            'features': "Key features: Menu management, Inventory, Orders, Sales analytics, Staff management, Customer feedback, and AI assistant.",
            'chatbot': "I'm your AI assistant! Ask me anything about the restaurant system.",
            'what can you do': "I can answer questions about menu, orders, inventory, sales, staff, admin, and more!",
        }

        # Flexible keyword matching
        response = None
        for key, resp in responses.items():
            if key in user_message:
                response = resp
                break

        # Fallback for unknown queries
        if not response:
            response = "I'm here to help with anything related to our restaurant system: menu, orders, inventory, sales, staff, admin, and more. Please rephrase your question or ask for 'help' to see what I can do!"

        logger.debug(f"Chatbot - User: {user_message} | Bot: {response}")
        return jsonify({'response': response, 'status': 'success'})
                                
    except Exception as e:
        logger.error(f"Chatbot error: {str(e)}")
        return jsonify({'response': "Sorry, an error occurred. Please try again.", 'status': 'error'}), 500

@app.route('/create_order', methods=['POST'])
@login_required
def create_order():
    try:
        data = request.get_json()
        logger.debug(f"Received order data: {data}")  # Debug log
        
        if not data or 'items' not in data:
            logger.error("Invalid order data received")  # Debug log
            return jsonify({'success': False, 'error': 'Invalid order data'})

        # Log all expected fields
        logger.debug(f"Customer Name: {data.get('customer_name')}")
        logger.debug(f"Order Date: {data.get('order_date')}")
        logger.debug(f"Total Amount: {data.get('total')}")
        logger.debug(f"Status: {data.get('status')}")
        logger.debug(f"Items: {data.get('items')}")
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'})

        try:
            cursor = conn.cursor(dictionary=True)
            
            # Create the order
            order_query = """
                INSERT INTO orders (Customer_Name, Order_Date, Total_Amount, Status)
                VALUES (%s, %s, %s, %s)
            """
            
            # Log the values being inserted
            values = (
                data.get('customer_name'),
                data.get('order_date'),
                data.get('total'),
                data.get('status')
            )
            logger.debug(f"Executing order query with values: {values}")  # Debug log
            
            cursor.execute(order_query, values)
            
            order_id = cursor.lastrowid
            logger.debug(f"Created order with ID: {order_id}")  # Debug log
            
            # Create order details for each item
            details_query = """
                INSERT INTO order_details (Order_ID, Item_ID, Item_Name, Quantity, Unit_Price, Subtotal)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            for item in data['items']:
                subtotal = float(item['price']) * int(item['quantity'])
                detail_values = (
                    order_id,
                    item['id'],
                    item['name'],
                    item['quantity'],
                    item['price'],
                    subtotal
                )
                logger.debug(f"Inserting order detail with values: {detail_values}")  # Debug log
                cursor.execute(details_query, detail_values)
            
            conn.commit()
            logger.info(f"Successfully created order {order_id} with {len(data['items'])} items")
            return jsonify({'success': True, 'order_id': order_id})
            
        except mysql.connector.Error as err:
            logger.error(f"Database error creating order: {err}")
            conn.rollback()
            return jsonify({'success': False, 'error': str(err)})
        finally:
            conn.close()
            logger.debug("Database connection closed")
        
    except Exception as e:
        logger.error(f"Error processing order: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/partners')
@login_required
def partners():
    return render_template('partners.html')

@app.route('/subscription')
@login_required
def subscription():
    return render_template('subscription.html')

@app.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    dish_id = request.form.get('dish_id')
    dish_name = request.form.get('dish_name')
    price = float(request.form.get('price'))
    
    if 'cart' not in session:
        session['cart'] = []
    
    # Check if item already exists in cart
    for item in session['cart']:
        if item['id'] == dish_id:
            item['quantity'] += 1
            break
    else:
        session['cart'].append({
            'id': dish_id,
            'name': dish_name,
            'price': price,
            'quantity': 1
        })
    
    session.modified = True
    return jsonify({'success': True, 'cart_count': len(session['cart'])})

@app.route('/checkout')
@login_required
def checkout():
    if 'cart' not in session or not session['cart']:
        flash('Your cart is empty', 'error')
        return redirect(url_for('menu'))
    
    cart_items = session['cart']
    total_amount = sum(item['price'] * item['quantity'] for item in cart_items)
    
    return render_template('checkout.html', 
                         cart_items=cart_items,
                         total_amount=total_amount)

@app.route('/process_checkout', methods=['POST'])
@login_required
def process_checkout():
    if 'cart' not in session or not session['cart']:
        flash('Your cart is empty', 'error')
        return redirect(url_for('menu'))
    
    try:
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection error', 'error')
            return redirect(url_for('checkout'))
        
        cursor = conn.cursor()
        
        # Insert customer details
        cursor.execute("""
            INSERT INTO Customer (Name, Phone_Number, Email)
            VALUES (%s, %s, %s)
        """, (name, phone, email))
        
        customer_id = cursor.lastrowid
        
        # Create order
        total_amount = sum(item['price'] * item['quantity'] for item in session['cart'])
        cursor.execute("""
            INSERT INTO Customer_Order (Customer_ID, Order_Date, Total_Amount)
            VALUES (%s, NOW(), %s)
        """, (customer_id, total_amount))
        
        order_id = cursor.lastrowid
        
        # Insert order items
        for item in session['cart']:
            cursor.execute("""
                INSERT INTO Order_Details (Order_ID, Dish_ID, Quantity)
                VALUES (%s, %s, %s)
            """, (order_id, item['id'], item['quantity']))
        
        conn.commit()
        
        # Clear the cart
        session.pop('cart', None)
        
        flash('Order placed successfully!', 'success')
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        logger.error(f"Checkout error: {str(e)}")
        if conn:
            conn.rollback()
        flash('An error occurred while processing your order', 'error')
        return redirect(url_for('checkout'))
    finally:
        if conn and conn.is_connected():
            conn.close()

@app.route('/update_order_status', methods=['POST'])
def update_order_status():
    order_id = request.json.get('order_id')
    new_status = request.json.get('new_status')
    if not order_id or not new_status:
        return jsonify({'success': False, 'error': 'Missing data'}), 400

    connection = get_db_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        
        # First try updating the simplified schema (orders table)
        try:
            cursor.execute("UPDATE orders SET Status = %s WHERE Order_ID = %s", (new_status, order_id))
            if cursor.rowcount > 0:
                connection.commit()
                return jsonify({'success': True})
        except mysql.connector.Error as e:
            logger.debug(f"Could not update simplified schema: {e}")
        
        # If simplified schema update fails, try the complex schema
        try:
            # Get the Status_ID from Order_Status table
            cursor.execute("SELECT Status_ID FROM Order_Status WHERE Status_Name = %s", (new_status,))
            row = cursor.fetchone()
            if not row:
                return jsonify({'success': False, 'error': 'Invalid status'}), 400
            status_id = row['Status_ID']
            
            # Update the order status using Status_ID
            cursor.execute("UPDATE Customer_Order SET Status_ID = %s WHERE Order_ID = %s", (status_id, order_id))
            connection.commit()
            return jsonify({'success': True})
        except mysql.connector.Error as e:
            logger.error(f"Could not update complex schema: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/create_batch', methods=['POST'])
@login_required
def create_batch():
    try:
        data = request.get_json()
        logger.debug(f"Received batch data: {data}")
        
        if not data or not all(k in data for k in ['item_name', 'quantity', 'expiry_date']):
            return jsonify({'success': False, 'error': 'Missing required fields'})
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'})
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            # First get the Item_ID from Inventory_Item
            cursor.execute("SELECT Item_ID FROM Inventory_Item WHERE Name = %s", (data['item_name'],))
            item = cursor.fetchone()
            
            if not item:
                return jsonify({'success': False, 'error': 'Item not found'})
            
            # Insert the new batch
            cursor.execute("""
                INSERT INTO Inventory_Batch (Item_ID, Quantity, Expiry_Date)
                VALUES (%s, %s, %s)
            """, (item['Item_ID'], data['quantity'], data['expiry_date']))
            
            # Update the total quantity in Inventory_Item
            cursor.execute("""
                UPDATE Inventory_Item 
                SET Quantity = Quantity + %s 
                WHERE Item_ID = %s
            """, (data['quantity'], item['Item_ID']))
            
            conn.commit()
            return jsonify({'success': True, 'message': 'Batch created successfully'})
            
        except mysql.connector.Error as err:
            logger.error(f"Database error creating batch: {err}")
            conn.rollback()
            return jsonify({'success': False, 'error': str(err)})
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Error creating batch: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/create_item', methods=['POST'])
@login_required
def create_item():
    try:
        data = request.get_json()
        logger.debug(f"Received new item data: {data}")
        required_fields = ['name', 'quantity', 'unit', 'reorder_level']
        if not data or not all(k in data for k in required_fields):
            return jsonify({'success': False, 'error': 'Missing required fields'})
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'})
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                INSERT INTO Inventory_Item (Name, Quantity, Unit, Reorder_Level)
                VALUES (%s, %s, %s, %s)
            """, (data['name'], data['quantity'], data['unit'], data['reorder_level']))
            conn.commit()
            return jsonify({'success': True, 'message': 'Item created successfully'})
        except mysql.connector.Error as err:
            logger.error(f"Database error creating item: {err}")
            conn.rollback()
            return jsonify({'success': False, 'error': str(err)})
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Error creating item: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/create_supplier', methods=['POST'])
@login_required
def create_supplier():
    try:
        data = request.get_json()
        logger.debug(f"Received new supplier data: {data}")
        required_fields = ['name', 'contact_info', 'items_supplied']
        if not data or not all(k in data for k in required_fields):
            return jsonify({'success': False, 'error': 'Missing required fields'})
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'})
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                INSERT INTO Supplier (Name, Contact_Info, Items_Supplied)
                VALUES (%s, %s, %s)
            """, (data['name'], data['contact_info'], data['items_supplied']))
            conn.commit()
            return jsonify({'success': True, 'message': 'Supplier created successfully'})
        except mysql.connector.Error as err:
            logger.error(f"Database error creating supplier: {err}")
            conn.rollback()
            return jsonify({'success': False, 'error': str(err)})
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Error creating supplier: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)