import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG
import logging
from decimal import Decimal

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def convert_decimal(obj):
    """Convert Decimal objects to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal(item) for item in obj]
    return obj

def get_db_connection():
    """Create and return a database connection"""
    try:
        logger.debug("Attempting to connect to database with config: %s", {k: v for k, v in DB_CONFIG.items() if k != 'password'})
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            db_info = connection.get_server_info()
            logger.debug(f"Connected to MySQL Server version {db_info}")
            cursor = connection.cursor()
            cursor.execute("select database();")
            db_name = cursor.fetchone()[0]
            logger.debug(f"Connected to database: {db_name}")
            cursor.close()
            return connection
    except Error as e:
        logger.error(f"Error connecting to MySQL Database: {e}")
        logger.error(f"Error type: {type(e)}")
        if hasattr(e, 'errno'):
            logger.error(f"Error number: {e.errno}")
        if hasattr(e, 'sqlstate'):
            logger.error(f"SQL state: {e.sqlstate}")
        if hasattr(e, 'msg'):
            logger.error(f"Error message: {e.msg}")
    except Exception as e:
        logger.error(f"Unexpected error during database connection: {e}")
        logger.error(f"Error type: {type(e)}")
    return None

def close_connection(connection, cursor=None):
    """Close database connection and cursor"""
    if cursor:
        cursor.close()
    if connection and connection.is_connected():
        connection.close()
        logger.debug("Database connection closed")

def fetch_all_dishes():
    """Fetch all dishes from the database"""
    connection = get_db_connection()
    if not connection:
        logger.error("Could not establish database connection")
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT Dish_ID as ID, Name, Price FROM Dish")
        results = cursor.fetchall()
        logger.debug(f"Fetched {len(results)} dishes from database")
        return convert_decimal(results)
    except Error as e:
        logger.error(f"Error fetching dishes: {e}")
        return []
    finally:
        close_connection(connection, cursor)

def fetch_ingredients():
    """Fetch all dish ingredients"""
    connection = get_db_connection()
    if not connection:
        logger.error("Could not establish database connection")
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT d.Name as Dish_Name, i.Name as Ingredient_Name, di.Quantity 
            FROM Dish_Ingredient di 
            JOIN Dish d ON di.Dish_ID = d.Dish_ID 
            JOIN Inventory_Item i ON di.Item_ID = i.Item_ID
        """)
        results = cursor.fetchall()
        logger.debug(f"Fetched {len(results)} ingredients from database")
        return results
    except Error as e:
        logger.error(f"Error fetching ingredients: {e}")
        return []
    finally:
        close_connection(connection, cursor)

def fetch_inventory():
    """Fetch current inventory"""
    connection = get_db_connection()
    if not connection:
        logger.error("Could not establish database connection")
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                Item_ID,
                Name,
                Quantity,
                Unit,
                Reorder_Level
            FROM Inventory_Item
            ORDER BY Name
        """)
        results = cursor.fetchall()
        logger.debug(f"Fetched {len(results)} inventory items from database")
        return convert_decimal(results)
    except Error as e:
        logger.error(f"Error fetching inventory: {e}")
        return []
    finally:
        close_connection(connection, cursor)

def fetch_batches():
    """Fetch inventory batches"""
    connection = get_db_connection()
    if not connection:
        logger.error("Could not establish database connection")
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                b.Batch_ID,
                i.Name as Item_Name,
                b.Quantity,
                b.Expiry_Date
            FROM Inventory_Batch b 
            JOIN Inventory_Item i ON b.Item_ID = i.Item_ID
            ORDER BY b.Expiry_Date ASC
        """)
        results = cursor.fetchall()
        logger.debug(f"Fetched {len(results)} batches from database")
        return convert_decimal(results)
    except Error as e:
        logger.error(f"Error fetching batches: {e}")
        return []
    finally:
        close_connection(connection, cursor)

def fetch_suppliers():
    """Fetch all suppliers"""
    connection = get_db_connection()
    if not connection:
        logger.error("Could not establish database connection")
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                Supplier_ID,
                Name,
                Contact_Info,
                (
                    SELECT GROUP_CONCAT(Name)
                    FROM Inventory_Item
                    WHERE Supplier_ID = s.Supplier_ID
                ) as Items_Supplied
            FROM Supplier s
        """)
        results = cursor.fetchall()
        logger.debug(f"Fetched {len(results)} suppliers from database")
        return results
    except Error as e:
        logger.error(f"Error fetching suppliers: {e}")
        return []
    finally:
        close_connection(connection, cursor)

def fetch_customers():
    """Fetch all customers"""
    connection = get_db_connection()
    if not connection:
        logger.error("Could not establish database connection")
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT Customer_ID as ID, Name, Phone_Number, Email FROM Customer")
        results = cursor.fetchall()
        logger.debug(f"Fetched {len(results)} customers from database")
        return results
    except Error as e:
        logger.error(f"Error fetching customers: {e}")
        return []
    finally:
        close_connection(connection, cursor)

def fetch_orders():
    """Fetch all orders with customer details and status"""
    connection = get_db_connection()
    if not connection:
        logger.error("Could not establish database connection")
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # First try the simplified schema
        try:
            cursor.execute("""
                SELECT 
                    o.Order_ID,
                    o.Customer_Name,
                    o.Order_Date,
                    o.Total_Amount,
                    o.Status
                FROM orders o
                ORDER BY o.Order_Date DESC
            """)
            results = cursor.fetchall()
            if results:
                logger.debug(f"Fetched {len(results)} orders from simplified schema")
                return convert_decimal(results)
        except mysql.connector.Error as e:
            logger.debug(f"Could not fetch from simplified schema: {e}")
        
        # If simplified schema fails, try the complex schema
        try:
            cursor.execute("""
                SELECT 
                    co.Order_ID,
                    COALESCE(c.Name, 'N/A') as Customer_Name,
                    co.Order_Date,
                    co.Total_Amount,
                    COALESCE(os.Status_Name, 'Pending') as Status
                FROM Customer_Order co
                LEFT JOIN Customer c ON co.Customer_ID = c.Customer_ID
                LEFT JOIN Order_Status os ON co.Status_ID = os.Status_ID
                ORDER BY co.Order_Date DESC
            """)
            results = cursor.fetchall()
            logger.debug(f"Fetched {len(results)} orders from complex schema")
            return convert_decimal(results)
        except mysql.connector.Error as e:
            logger.error(f"Could not fetch from complex schema: {e}")
            return []
            
    except Error as e:
        logger.error(f"Error fetching orders: {e}")
        return []
    finally:
        close_connection(connection, cursor)

def fetch_sales():
    """Fetch sales analysis"""
    connection = get_db_connection()
    if not connection:
        logger.error("Could not establish database connection")
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                s.Sale_ID,
                d.Name as Item_Name,
                s.Sale_Date,
                s.Quantity_Sold,
                (s.Quantity_Sold * d.Price) as Revenue
            FROM Sales s
            JOIN Dish d ON s.Dish_ID = d.Dish_ID
            ORDER BY s.Sale_Date DESC
        """)
        results = cursor.fetchall()
        logger.debug(f"Fetched {len(results)} sales records from database")
        return convert_decimal(results)
    except Error as e:
        logger.error(f"Error fetching sales: {e}")
        return []
    finally:
        close_connection(connection, cursor)

def fetch_login_history():
    """Fetch login history records"""
    connection = get_db_connection()
    if not connection:
        logger.error("Could not establish database connection")
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT username, login_datetime
            FROM login_history
            ORDER BY login_datetime DESC
            LIMIT 50
        """)
        results = cursor.fetchall()
        logger.debug(f"Fetched {len(results)} login history records from database")
        return results
    except Error as e:
        logger.error(f"Error fetching login history: {e}")
        return []
    finally:
        close_connection(connection, cursor) 

def fetch_inventory_with_usage():
    """Fetch inventory items with their usage statistics"""
    connection = get_db_connection()
    if not connection:
        logger.error("Could not establish database connection")
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                i.Item_ID,
                i.Name,
                i.Quantity,
                i.Unit,
                i.Reorder_Level,
                COALESCE(
                    (SELECT SUM(iu.Quantity_Used)
                     FROM Inventory_Usage iu 
                     WHERE iu.Item_ID = i.Item_ID 
                     AND DATE(iu.Usage_Date) = CURDATE()
                    ), 0
                ) as Used_Today
            FROM Inventory_Item i
            ORDER BY i.Name
        """)
        results = cursor.fetchall()
        logger.debug(f"Fetched {len(results)} inventory items with usage from database")
        return results
    except Error as e:
        logger.error(f"Error fetching inventory with usage: {e}")
        return []
    finally:
        close_connection(connection, cursor)

def fetch_recent_orders():
    """Fetch recent order details with status"""
    connection = get_db_connection()
    if not connection:
        logger.error("Could not establish database connection")
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # First try the simplified schema
        try:
            cursor.execute("""
                SELECT 
                    od.Detail_ID as OrderDetail_ID,
                    od.Order_ID,
                    od.Item_Name,
                    od.Quantity,
                    od.Unit_Price,
                    od.Subtotal,
                    o.Order_Date,
                    o.Status
                FROM order_details od
                JOIN orders o ON od.Order_ID = o.Order_ID
                ORDER BY o.Order_Date DESC
                LIMIT 50
            """)
            results = cursor.fetchall()
            if results:
                logger.debug(f"Fetched {len(results)} order details from simplified schema")
                return convert_decimal(results)
        except mysql.connector.Error as e:
            logger.debug(f"Could not fetch from simplified schema: {e}")
        
        # If simplified schema fails, try the complex schema
        try:
            cursor.execute("""
                SELECT 
                    od.OrderDetail_ID,
                    od.Order_ID,
                    d.Name as Item_Name,
                    od.Quantity,
                    d.Price as Unit_Price,
                    (od.Quantity * d.Price) as Subtotal,
                    co.Order_Date,
                    COALESCE(os.Status_Name, 'Pending') as Status
                FROM Order_Details od
                JOIN Dish d ON od.Dish_ID = d.Dish_ID
                JOIN Customer_Order co ON od.Order_ID = co.Order_ID
                LEFT JOIN Order_Status os ON co.Status_ID = os.Status_ID
                ORDER BY co.Order_Date DESC
                LIMIT 50
            """)
            results = cursor.fetchall()
            logger.debug(f"Fetched {len(results)} order details from complex schema")
            return convert_decimal(results)
        except mysql.connector.Error as e:
            logger.error(f"Could not fetch from complex schema: {e}")
            return []
            
    except Error as e:
        logger.error(f"Error fetching order details: {e}")
        return []
    finally:
        close_connection(connection, cursor)

def verify_admin_login(username, password):
    """Verify admin login credentials"""
    connection = get_db_connection()
    if not connection:
        logger.error("Could not establish database connection")
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM admin 
            WHERE username = %s AND password = %s
        """, (username, password))
        admin = cursor.fetchone()
        logger.debug(f"Admin login attempt for {username}: {'success' if admin else 'failed'}")
        return admin
    except Error as e:
        logger.error(f"Error verifying admin login: {e}")
        return None
    finally:
        close_connection(connection, cursor)

def verify_staff_login(username, password):
    """Verify staff login credentials"""
    connection = get_db_connection()
    if not connection:
        logger.error("Could not establish database connection")
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM staff 
            WHERE username = %s AND password = %s
        """, (username, password))
        staff = cursor.fetchone()
        logger.debug(f"Staff login attempt for {username}: {'success' if staff else 'failed'}")
        return staff
    except Error as e:
        logger.error(f"Error verifying staff login: {e}")
        return None
    finally:
        close_connection(connection, cursor) 

def log_user_activity(user_id, username, role, action, action_details=None, ip_address=None, status='success'):
    """Log user activities"""
    connection = get_db_connection()
    if not connection:
        logger.error("Could not establish database connection")
        return False
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO UserActivityLog 
            (User_ID, Username, Role, Action, Action_Details, IP_Address, Status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, username, role, action, action_details, ip_address, status))
        connection.commit()
        logger.debug(f"Logged activity for user {username}: {action}")
        return True
    except Error as e:
        logger.error(f"Error logging user activity: {e}")
        return False
    finally:
        close_connection(connection, cursor)

def log_login(user_id, username, role, ip_address=None, status='success'):
    """Log user login"""
    connection = get_db_connection()
    if not connection:
        logger.error("Could not establish database connection")
        return None
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO LoginHistory 
            (User_ID, Username, Role, IP_Address, Login_Status)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, username, role, ip_address, status))
        connection.commit()
        
        # Get the login ID
        login_id = cursor.lastrowid
        logger.debug(f"Logged login for user {username}")
        return login_id
    except Error as e:
        logger.error(f"Error logging login: {e}")
        return None
    finally:
        close_connection(connection, cursor)

def log_logout(login_id):
    """Log user logout and calculate session duration"""
    connection = get_db_connection()
    if not connection:
        logger.error("Could not establish database connection")
        return False
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE LoginHistory 
            SET Logout_Time = CURRENT_TIMESTAMP,
                Session_Duration = TIMESTAMPDIFF(SECOND, Login_Time, CURRENT_TIMESTAMP)
            WHERE Login_ID = %s
        """, (login_id,))
        connection.commit()
        logger.debug(f"Logged logout for login ID {login_id}")
        return True
    except Error as e:
        logger.error(f"Error logging logout: {e}")
        return False
    finally:
        close_connection(connection, cursor)

def get_user_activity_logs(user_id=None, role=None, start_date=None, end_date=None, limit=100):
    """Fetch user activity logs with optional filters"""
    connection = get_db_connection()
    if not connection:
        logger.error("Could not establish database connection")
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM UserActivityLog WHERE 1=1"
        params = []
        
        if user_id:
            query += " AND User_ID = %s"
            params.append(user_id)
        if role:
            query += " AND Role = %s"
            params.append(role)
        if start_date:
            query += " AND Timestamp >= %s"
            params.append(start_date)
        if end_date:
            query += " AND Timestamp <= %s"
            params.append(end_date)
            
        query += " ORDER BY Timestamp DESC LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, tuple(params))
        results = cursor.fetchall()
        logger.debug(f"Fetched {len(results)} activity logs")
        return results
    except Error as e:
        logger.error(f"Error fetching activity logs: {e}")
        return []
    finally:
        close_connection(connection, cursor)

def get_login_history(user_id=None, role=None, start_date=None, end_date=None, limit=100):
    """Fetch login history with optional filters"""
    connection = get_db_connection()
    if not connection:
        logger.error("Could not establish database connection")
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM LoginHistory WHERE 1=1"
        params = []
        
        if user_id:
            query += " AND User_ID = %s"
            params.append(user_id)
        if role:
            query += " AND Role = %s"
            params.append(role)
        if start_date:
            query += " AND Login_Time >= %s"
            params.append(start_date)
        if end_date:
            query += " AND Login_Time <= %s"
            params.append(end_date)
            
        query += " ORDER BY Login_Time DESC LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, tuple(params))
        results = cursor.fetchall()
        logger.debug(f"Fetched {len(results)} login history records")
        return results
    except Error as e:
        logger.error(f"Error fetching login history: {e}")
        return []
    finally:
        close_connection(connection, cursor) 