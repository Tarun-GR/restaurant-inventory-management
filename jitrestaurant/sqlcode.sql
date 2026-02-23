-- ==============================
-- TABLE: Inventory_Item
-- ==============================
CREATE TABLE Inventory_Item (
    Item_ID INT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Quantity INT NOT NULL,
    Unit VARCHAR(50),
    Reorder_Level INT
);

-- ==============================
-- TABLE: Inventory_Batch
-- ==============================
CREATE TABLE Inventory_Batch (
    Batch_ID INT PRIMARY KEY,
    Item_ID INT,
    Quantity INT NOT NULL,
    Expiry_Date DATE,
    FOREIGN KEY (Item_ID) REFERENCES Inventory_Item(Item_ID)
);

-- ==============================
-- TABLE: Supplier
-- ==============================
CREATE TABLE Supplier (
    Supplier_ID INT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Contact_Info TEXT
);

-- (OPTIONAL RELATIONSHIP: Supplier supplies Inventory_Items)
-- You can create a junction table if many-to-many:
-- CREATE TABLE Supplier_Item (
--     Supplier_ID INT,
--     Item_ID INT,
--     PRIMARY KEY (Supplier_ID, Item_ID),
--     FOREIGN KEY (Supplier_ID) REFERENCES Supplier(Supplier_ID),
--     FOREIGN KEY (Item_ID) REFERENCES Inventory_Item(Item_ID)
-- );

-- ==============================
-- TABLE: Dish
-- ==============================
CREATE TABLE Dish (
    Dish_ID INT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Price DECIMAL(10, 2) NOT NULL
);

-- ==============================
-- TABLE: Dish_Ingredient
-- ==============================
CREATE TABLE Dish_Ingredient (
    DishIngredient_ID INT PRIMARY KEY,
    Dish_ID INT,
    Item_ID INT,
    Quantity INT NOT NULL,
    FOREIGN KEY (Dish_ID) REFERENCES Dish(Dish_ID),
    FOREIGN KEY (Item_ID) REFERENCES Inventory_Item(Item_ID)
);

-- ==============================
-- TABLE: Customer
-- ==============================
CREATE TABLE Customer (
    Customer_ID INT PRIMARY KEY,
    Name VARCHAR(100),
    Phone_Number VARCHAR(20),
    Email VARCHAR(100)
);

-- ==============================
-- TABLE: Order_Status
-- ==============================
CREATE TABLE Order_Status (
    Status_ID INT PRIMARY KEY,
    Status_Name VARCHAR(50) NOT NULL,
    Description TEXT
);

-- Insert default statuses
INSERT INTO Order_Status (Status_ID, Status_Name, Description) VALUES
(1, 'Pending', 'Order has been placed but not yet processed'),
(2, 'Preparing', 'Order is being prepared in the kitchen'),
(3, 'Ready', 'Order is ready for pickup/delivery'),
(4, 'Served', 'Order has been served to the customer'),
(5, 'Cancelled', 'Order has been cancelled');

-- ==============================
-- TABLE: Customer_Order
-- ==============================
CREATE TABLE Customer_Order (
    Order_ID INT PRIMARY KEY,
    Customer_ID INT,
    Order_Date DATETIME,
    Total_Amount DECIMAL(10, 2),
    Status_ID INT DEFAULT 1,
    FOREIGN KEY (Customer_ID) REFERENCES Customer(Customer_ID),
    FOREIGN KEY (Status_ID) REFERENCES Order_Status(Status_ID)
);

-- ==============================
-- TABLE: Order_Details
-- ==============================
CREATE TABLE Order_Details (
    OrderDetail_ID INT PRIMARY KEY,
    Order_ID INT,
    Dish_ID INT,
    Quantity INT NOT NULL,
    FOREIGN KEY (Order_ID) REFERENCES Customer_Order(Order_ID),
    FOREIGN KEY (Dish_ID) REFERENCES Dish(Dish_ID)
);

-- ==============================
-- TABLE: Sales
-- ==============================
CREATE TABLE Sales (
    Sale_ID INT PRIMARY KEY,
    Dish_ID INT,
    Sale_Date DATE,
    Quantity_Sold INT,
    FOREIGN KEY (Dish_ID) REFERENCES Dish(Dish_ID)
);
-- ==============================
-- DATA INSERTION
-- ==============================
-- ===========================
-- Inventory_Item
-- ===========================
INSERT INTO Inventory_Item (Item_ID, Name, Quantity, Unit, Reorder_Level) VALUES
(1, 'Chicken Breast', 200, 'kg', 50),
(2, 'Tomato', 150, 'kg', 30),
(3, 'Onion', 100, 'kg', 25),
(4, 'Cheese', 80, 'kg', 20),
(5, 'Lettuce', 60, 'kg', 15);

-- ===========================
-- Inventory_Batch
-- ===========================
INSERT INTO Inventory_Batch (Batch_ID, Item_ID, Quantity, Expiry_Date) VALUES
(1, 1, 100, '2025-05-15'),
(2, 2, 50, '2025-04-30'),
(3, 3, 30, '2025-05-10'),
(4, 4, 40, '2025-06-01'),
(5, 5, 20, '2025-04-29');

-- ===========================
-- Supplier
-- ===========================
INSERT INTO Supplier (Supplier_ID, Name, Contact_Info) VALUES
(1, 'FreshFarm Foods', 'freshfarm@example.com'),
(2, 'Urban Veggies Ltd', 'urbanveg@example.com'),
(3, 'Meat Masters', 'meatmaster@example.com');

-- ===========================
-- Dish
-- ===========================
INSERT INTO Dish (Dish_ID, Name, Price) VALUES
(1, 'Spicy Chicken Wings', 12.99),
(2, 'Cheese Tomato Sandwich', 6.49),
(3, 'Grilled Chicken Salad', 10.00),
(4, 'Veggie Wrap', 8.50);

-- ===========================
-- Dish_Ingredient
-- ===========================
INSERT INTO Dish_Ingredient (DishIngredient_ID, Dish_ID, Item_ID, Quantity) VALUES
(1, 1, 1, 2),
(2, 1, 3, 1),
(3, 2, 2, 1),
(4, 2, 4, 1),
(5, 3, 1, 1),
(6, 3, 5, 1),
(7, 4, 2, 1),
(8, 4, 5, 1);

-- ===========================
-- Customer
-- ===========================
INSERT INTO Customer (Customer_ID, Name, Phone_Number, Email) VALUES
(1, 'Alice Johnson', '555-1234', 'alice@example.com'),
(2, 'Bob Smith', '555-5678', 'bob@example.com'),
(3, 'Charlie Rose', '555-8765', 'charlie@example.com');

-- ===========================
-- Customer_Order
-- ===========================
INSERT INTO Customer_Order (Order_ID, Customer_ID, Order_Date, Total_Amount) VALUES
(101, 1, '2025-04-25 12:30:00', 25.98),
(102, 2, '2025-04-25 18:15:00', 10.00),
(103, 1, '2025-04-26 13:00:00', 12.99),
(104, 3, '2025-04-26 19:30:00', 19.49);

-- ===========================
-- Order_Details
-- ===========================
INSERT INTO Order_Details (OrderDetail_ID, Order_ID, Dish_ID, Quantity) VALUES
(201, 101, 1, 2),
(202, 102, 3, 1),
(203, 103, 1, 1),
(204, 104, 3, 1),
(205, 104, 4, 1);

-- ===========================
-- Sales
-- ===========================
INSERT INTO Sales (Sale_ID, Dish_ID, Sale_Date, Quantity_Sold) VALUES
(301, 1, '2025-04-25', 15),
(302, 2, '2025-04-25', 10),
(303, 3, '2025-04-25', 8),
(304, 1, '2025-04-26', 20),
(305, 4, '2025-04-26', 6);

-- ===========================
-- Additional Inventory_Item
-- ===========================
INSERT INTO Inventory_Item (Item_ID, Name, Quantity, Unit, Reorder_Level) VALUES
(6, 'Beef Patty', 120, 'kg', 30),
(7, 'Burger Bun', 300, 'pieces', 100),
(8, 'Pickles', 60, 'kg', 20);

-- ===========================
-- Additional Inventory_Batch
-- ===========================
INSERT INTO Inventory_Batch (Batch_ID, Item_ID, Quantity, Expiry_Date) VALUES
(6, 6, 50, '2025-05-15'),
(7, 7, 200, '2025-06-01'),
(8, 8, 30, '2025-05-10');

-- ===========================
-- Additional Suppliers
-- ===========================
INSERT INTO Supplier (Supplier_ID, Name, Contact_Info) VALUES
(4, 'Pickle Partners', 'pickles@example.com'),
(5, 'Bun Bakers', 'buns@example.com');

-- ===========================
-- Additional Dishes
-- ===========================
INSERT INTO Dish (Dish_ID, Name, Price) VALUES
(5, 'Beef Burger', 11.99),
(6, 'Pickle Platter', 5.49);

-- ===========================
-- Additional Dish_Ingredients
-- ===========================
INSERT INTO Dish_Ingredient (DishIngredient_ID, Dish_ID, Item_ID, Quantity) VALUES
(9, 5, 6, 1),
(10, 5, 7, 1),
(11, 5, 8, 1),
(12, 6, 8, 2);

-- ===========================
-- Additional Customers
-- ===========================
INSERT INTO Customer (Customer_ID, Name, Phone_Number, Email) VALUES
(4, 'Diana Prince', '555-0001', 'diana@example.com'),
(5, 'Ethan Hunt', '555-0002', 'ethan@example.com');

-- ===========================
-- Additional Customer Orders
-- ===========================
INSERT INTO Customer_Order (Order_ID, Customer_ID, Order_Date, Total_Amount) VALUES
(105, 4, '2025-04-27 12:45:00', 17.48),
(106, 5, '2025-04-27 18:30:00', 23.98),
(107, 1, '2025-04-28 13:10:00', 5.49);

-- ===========================
-- Additional Order Details
-- ===========================
INSERT INTO Order_Details (OrderDetail_ID, Order_ID, Dish_ID, Quantity) VALUES
(206, 105, 5, 1),
(207, 105, 6, 1),
(208, 106, 1, 2),
(209, 107, 6, 1);

-- ===========================
-- Additional Sales Records
-- ===========================
INSERT INTO Sales (Sale_ID, Dish_ID, Sale_Date, Quantity_Sold) VALUES
(306, 5, '2025-04-27', 12),
(307, 6, '2025-04-27', 5),
(308, 1, '2025-04-27', 18),
(309, 6, '2025-04-28', 3);
