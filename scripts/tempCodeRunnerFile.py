import os
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder
import mysql.connector
import yaml
from sqlalchemy import create_engine

def fetch_basket_data():
    """Fetch basket data from the database."""
    conn = None  # Initialize connection variable
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, '..', 'config', 'db_config.yaml')
        
        # Load database configuration
        with open(config_path) as f:
            config = yaml.safe_load(f).get('mysql', {})
        
        # Ensure config is not empty
        if not config:
            raise ValueError("Database configuration is missing or invalid.")
        
        # Correct the host value
        host = config.get('host', '127.0.0.1').strip()
        if '@' in host:
            raise ValueError(f"Invalid host value: {host}. Host should not contain '@'.")
        
        # Create SQLAlchemy engine
        db_url = f"mysql+mysqlconnector://{config['user']}:{config['password']}@{host}:{config['port']}/{config['database']}"
        engine = create_engine(db_url, connect_args={'connect_timeout': 10})
        print("SQLAlchemy engine created successfully.")
        
        # Execute SQL query
        query = """
            SELECT 
                invoice_id AS invoice_no,  -- Correct column name if needed
                GROUP_CONCAT(product_id) AS basket
            FROM transactions
            GROUP BY invoice_id
            HAVING COUNT(product_id) > 1
        """
        df = pd.read_sql(query, engine)
        
        # Return processed data
        return df['basket'].str.split(',')
    
    except Exception as e:
        print(f"Data retrieval failed: {str(e)}")
        return None  # Return None in case of failure
    
    finally:
        # Close the connection if it was successfully opened
        if conn:
            conn.close()

def generate_rules():
    """Generate association rules."""
    try:
        # Fetch basket data
        baskets = fetch_basket_data()
        if baskets is None:
            print("Failed to fetch basket data. Exiting.")
            return
        
        if not baskets:
            print("No transactions found. Exiting.")
            return
        
        te = TransactionEncoder()
        te_ary = te.fit(baskets).transform(baskets)
        ohe_df = pd.DataFrame(te_ary, columns=te.columns_)
        
        # Dynamic support calculation
        num_transactions = len(ohe_df)
        if num_transactions == 0:
            print("No transactions available after encoding. Exiting.")
            return
        
        min_support = max(0.01, 50 / num_transactions)
        
        # Apriori algorithm
        frequent_itemsets = apriori(
            ohe_df, 
            min_support=min_support,
            use_colnames=True,
            low_memory=True
        )
        
        if frequent_itemsets.empty:
            print("No frequent itemsets found. Exiting.")
            return
        
        # Rule generation
        rules = association_rules(
            frequent_itemsets, 
            metric="conviction", 
            min_threshold=1.2
        )
        
        if rules.empty:
            print("No association rules generated. Exiting.")
            return
        
        # Filter for business rules
        final_rules = rules[
            (rules['confidence'] >= 0.4) &
            (rules['lift'] >= 1.5) &
            (rules['support'] >= 0.02)
        ].sort_values('leverage', ascending=False)
        
        if final_rules.empty:
            print("No rules met the business criteria. Exiting.")
            return
        
        # Save rules
        base_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(base_dir, '..', 'data', 'processed', 'association_rules.csv')
        final_rules.to_csv(output_path, index=False)
        print(f"Generated {len(final_rules)} association rules and saved to {output_path}")
    
    except Exception as e:
        print(f"Rule generation failed: {str(e)}")
    
if __name__ == "__main__":
    generate_rules()
