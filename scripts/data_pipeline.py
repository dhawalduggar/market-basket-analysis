import mysql.connector
import pandas as pd
import yaml
import os

def setup_database():
    """Create database and tables for the project"""
    try:
        # Load configuration file
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, '..', 'config', 'db_config.yaml')
        
        with open(config_path) as f:
            config = yaml.safe_load(f)['mysql']
        
        # Connect to MySQL without specifying a database
        conn = mysql.connector.connect(
            host=config['host'],
            user=config['user'],
            password=config['password']
        )
        cursor = conn.cursor()
        
        # Create database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config['database']}")
        
        # Switch to the created database
        conn.database = config['database']
        
        # Drop and recreate the transactions table
        cursor.execute("DROP TABLE IF EXISTS transactions")
        cursor.execute("""
            CREATE TABLE transactions (
                invoice_no VARCHAR(20) NOT NULL,
                product_id VARCHAR(50) NOT NULL,
                quantity INT,
                unit_price DECIMAL(10,2),
                customer_id VARCHAR(20),
                country VARCHAR(50),
                INDEX invoice_product_idx (invoice_no, product_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        
        # Create products table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id VARCHAR(50) PRIMARY KEY,
                description TEXT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        
        conn.commit()
        print("Database schema created successfully")
        
    except Exception as e:
        print(f"Database setup failed: {str(e)}")
    finally:
        cursor.close()
        conn.close()

def load_data():
    """Load cleaned data into MySQL tables"""
    try:
        # Load configuration file
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, '..', 'config', 'db_config.yaml')
        
        with open(config_path) as f:
            config = yaml.safe_load(f)['mysql']
        
        # Load cleaned retail data from CSV
        data_path = os.path.join(base_dir, '..', 'data', 'processed', 'cleaned_retail.csv')
        df = pd.read_csv(data_path)

        # In load_data() function, before validation:
        print("Actual CSV columns:", df.columns.tolist())
        
        # Verify DataFrame columns match schema
        expected_columns = ['invoice_no', 'product_id', 'quantity', 'unit_price', 'customer_id', 'country']
        if not all(col in df.columns for col in expected_columns):
            raise ValueError(f"DataFrame columns do not match expected schema: {expected_columns}")
        
        # Connect to MySQL database
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        # Batch insert transactions into MySQL
        batch_size = 1000
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            values = [tuple(row) for row in batch[['invoice_no', 'product_id', 'quantity', 'unit_price', 'customer_id', 'country']].values]
            
            cursor.executemany("""
                INSERT INTO transactions 
                (invoice_no, product_id, quantity, unit_price, customer_id, country)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, values)
            conn.commit()
        
        print(f"Loaded {len(df)} transactions successfully")
        
    except Exception as e:
        print(f"Data loading failed: {str(e)}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    setup_database()
    load_data()
