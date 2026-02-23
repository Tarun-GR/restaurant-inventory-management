import mysql.connector
from config import DB_CONFIG
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_tables():
    try:
        # Connect to the database
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        logger.info("Creating orders and order_details tables...")
        
        # Create orders table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            Order_ID INT AUTO_INCREMENT PRIMARY KEY,
            Customer_Name VARCHAR(100) NOT NULL,
            Order_Date DATETIME NOT NULL,
            Total_Amount DECIMAL(10, 2) NOT NULL,
            Status VARCHAR(50) NOT NULL DEFAULT 'Order Placed',
            Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create order_details table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_details (
            Detail_ID INT AUTO_INCREMENT PRIMARY KEY,
            Order_ID INT NOT NULL,
            Item_ID INT NOT NULL,
            Item_Name VARCHAR(100) NOT NULL,
            Quantity INT NOT NULL,
            Unit_Price DECIMAL(10, 2) NOT NULL,
            Subtotal DECIMAL(10, 2) NOT NULL,
            Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (Order_ID) REFERENCES orders(Order_ID) ON DELETE CASCADE
        )
        """)
        
        conn.commit()
        logger.info("Tables created successfully!")
        
    except mysql.connector.Error as err:
        logger.error(f"Error creating tables: {err}")
        raise
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            logger.info("Database connection closed.")

if __name__ == "__main__":
    create_tables() 