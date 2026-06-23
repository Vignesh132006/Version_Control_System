import mysql.connector
from mysql.connector import errorcode

import os

DB_NAME = os.environ.get('DB_NAME', 'version_system')
TABLE_NAME = os.environ.get('DB_TABLE_NAME', 'version_history')

# Connection details
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', 'Pinky@143'),
    'port': int(os.environ.get('DB_PORT', 3306))
}

def setup_database():
    print("Connecting to MySQL server...")
    try:
        # Connect to MySQL server without database first
        db = mysql.connector.connect(**DB_CONFIG)
        cursor = db.cursor()
    except mysql.connector.Error as err:
        print(f"[ERROR] Error connecting to MySQL: {err}")
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Please check your username and password.")
        elif err.errno == 2003: # Can't connect to MySQL server
            print("Please ensure your MySQL service is running.")
        return False

    try:
        # Create database if it does not exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        print(f"[OK] Database '{DB_NAME}' checked/created.")
        
        # Select the database
        db.database = DB_NAME
        
        # Create table if it does not exist
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            version_no INT NOT NULL,
            file_name VARCHAR(255) NOT NULL,
            created_at DATETIME NOT NULL
        ) ENGINE=InnoDB;
        """
        cursor.execute(create_table_query)
        print(f"[OK] Table '{TABLE_NAME}' checked/created.")
        
        db.commit()
        return True
        
    except mysql.connector.Error as err:
        print(f"[ERROR] Database setup error: {err}")
        return False
    finally:
        cursor.close()
        db.close()
        print("Connection closed.")

if __name__ == "__main__":
    print("--- Database Setup ---")
    if setup_database():
        print("[SUCCESS] Database setup completed successfully!")
    else:
        print("[ERROR] Database setup failed.")
