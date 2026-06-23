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

def setup_sqlite_database():
    import sqlite3
    try:
        db = sqlite3.connect("version_system.db")
        cursor = db.cursor()
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version_no INT NOT NULL,
            file_name VARCHAR(255) NOT NULL,
            created_at DATETIME NOT NULL
        );
        """
        cursor.execute(create_table_query)
        db.commit()
        print("[OK] SQLite Database version_system.db checked/created.")
        return True
    except Exception as e:
        print(f"[ERROR] SQLite setup failed: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()

def setup_database():
    db_host = os.environ.get("DB_HOST", "")
    if not db_host:
        print("[INFO] No DB_HOST environment variable configured. Falling back to SQLite setup...")
        return setup_sqlite_database()

    print("Connecting to MySQL server...")
    try:
        # Connect to MySQL server without database first
        db = mysql.connector.connect(**DB_CONFIG)
        cursor = db.cursor()
    except mysql.connector.Error as err:
        print(f"[WARNING] Error connecting to MySQL: {err}")
        print("Falling back to SQLite database setup...")
        return setup_sqlite_database()

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
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'db' in locals() and db:
            db.close()
        print("Connection closed.")

if __name__ == "__main__":
    print("--- Database Setup ---")
    if setup_database():
        print("[SUCCESS] Database setup completed successfully!")
    else:
        print("[ERROR] Database setup failed.")
