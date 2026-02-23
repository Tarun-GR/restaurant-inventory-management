from database import get_db_connection
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def check_database():
    connection = get_db_connection()
    if not connection:
        print("Could not connect to database")
        return
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Check Customer table
        cursor.execute("SELECT COUNT(*) as count FROM Customer")
        customer_count = cursor.fetchone()['count']
        print(f"Customers in database: {customer_count}")
        
        # Check Customer_Order table
        cursor.execute("SELECT COUNT(*) as count FROM Customer_Order")
        order_count = cursor.fetchone()['count']
        print(f"Orders in database: {order_count}")
        
        if order_count > 0:
            # Check a sample order
            cursor.execute("""
                SELECT co.*, c.Name as Customer_Name 
                FROM Customer_Order co 
                JOIN Customer c ON co.Customer_ID = c.Customer_ID 
                LIMIT 1
            """)
            sample_order = cursor.fetchone()
            print("\nSample Order:")
            print(sample_order)
        
        # Check Order_Details table
        cursor.execute("SELECT COUNT(*) as count FROM Order_Details")
        details_count = cursor.fetchone()['count']
        print(f"\nOrder details in database: {details_count}")
        
        if details_count > 0:
            # Check sample order details
            cursor.execute("""
                SELECT od.*, d.Name as Dish_Name 
                FROM Order_Details od 
                JOIN Dish d ON od.Dish_ID = d.Dish_ID 
                LIMIT 1
            """)
            sample_details = cursor.fetchone()
            print("\nSample Order Details:")
            print(sample_details)
            
    except Exception as e:
        print(f"Error checking database: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    check_database() 