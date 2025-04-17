import pandas as pd
import mysql.connector
import yaml
import os

def export_visualization_data():
    """Prepare data for Power BI"""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, '..', 'config', 'db_config.yaml')
        
        # Load database configuration
        with open(config_path) as f:
            config = yaml.safe_load(f)['mysql']
        
        # Connect to MySQL database
        conn = mysql.connector.connect(**config)
        
        # Transaction metrics
        transactions = pd.read_sql("""
            SELECT
                invoice_no,
                SUM(quantity * unit_price) AS transaction_value,
                COUNT(DISTINCT product_id) AS unique_products
            FROM transactions
            GROUP BY invoice_no
        """, conn)
        
        # Association rules
        rules_path = os.path.join(base_dir, '..', 'data', 'processed', 'association_rules.csv')
        if os.path.exists(rules_path):
            rules = pd.read_csv(rules_path)
        else:
            print(f"Association rules file not found at {rules_path}. Skipping rules export.")
            rules = pd.DataFrame()  # Empty DataFrame if file doesn't exist
        
        # Customer segments
        customers = pd.read_sql("""
            SELECT
                customer_id,
                COUNT(DISTINCT invoice_no) AS transaction_count,
                SUM(quantity * unit_price) AS total_spend
            FROM transactions
            GROUP BY customer_id
        """, conn)
        
        # Save outputs
        transactions.to_csv(os.path.join(base_dir, '..', 'data', 'processed', 'pbi_transactions.csv'), index=False)
        if not rules.empty:
            rules.to_csv(os.path.join(base_dir, '..', 'data', 'processed', 'pbi_rules.csv'), index=False)
        customers.to_csv(os.path.join(base_dir, '..', 'data', 'processed', 'pbi_customers.csv'), index=False)
        
        print("Power BI data exported successfully")
        
    except Exception as e:
        print(f"Export failed: {str(e)}")
    finally:
        if conn.is_connected():
            conn.close()

if __name__ == "__main__":
    export_visualization_data()
