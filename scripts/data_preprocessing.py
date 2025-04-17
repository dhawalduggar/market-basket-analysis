import pandas as pd
import os

def clean_dataset():
    """Clean and prepare retail data"""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        input_path = os.path.join(base_dir, '..', 'data', 'external', 'online_retail_II.xlsx')
        output_path = os.path.join(base_dir, '..', 'data', 'processed', 'cleaned_retail.csv')
        
        # Load data
        df = pd.read_excel(input_path, sheet_name='Year 2010-2011')
        
        # Standardize column names by stripping whitespace
        df.columns = df.columns.str.strip()
        
        # Critical cleaning
        df = df[~df['Invoice'].astype(str).str.startswith('C')]  # Remove cancellations
        df = df[df['Quantity'] > 0]                             # Remove returns
        df = df[df['Customer ID'].notna()]                      # Remove guest checkouts
        df = df[df['Price'] > 5.0]                              # Focus on premium items
        
        # Standardize columns (exclude 'description')
        df = df.rename(columns={
            'Invoice': 'invoice_no',
            'StockCode': 'product_id',
            'Quantity': 'quantity',
            'Price': 'unit_price',
            'Customer ID': 'customer_id',
            'Country': 'country'
        })[['invoice_no', 'product_id', 'quantity', 'unit_price', 'customer_id', 'country']]
        
        df.to_csv(output_path, index=False)
        print(f"Cleaned data saved to {output_path}")
        
    except Exception as e:
        print(f"Cleaning failed: {str(e)}")

if __name__ == "__main__":
    clean_dataset()
