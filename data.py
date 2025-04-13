# data.py
# Import required libraries
from flask import Flask, request, jsonify, send_file, render_template
import pandas as pd
import numpy as np
import os
import glob
from glob import glob
from datetime import datetime, timedelta
import psycopg2
import psycopg2.extras
import matplotlib.pyplot as plt
import seaborn as sns
import io
import time
import concurrent.futures
import logging
import csv
from sqlalchemy import create_engine, text
import plotly.express as px
import plotly.graph_objects as go
import shutil
from dotenv import load_dotenv
import json
import traceback
import pandas as pd
import os
import glob
import logging
import json
from datetime import datetime
import numpy as np
import zipfile
from flask import send_file
from io import BytesIO

# Import chatbot functionality
from chatbot import SalesDataChatbot  # Import the chat route handler

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask application setup
app = Flask(__name__)
chatbot = SalesDataChatbot()

# Define constants
TEMP_STORAGE_DIR = "temp_storage"
PROCESSED_DIR = "processed_data"
MASTER_SUMMARY_FILE = "master_summary.xlsx"
DB_RETENTION_DAYS = 30

# Create necessary directories if they don’t exist
for directory in [TEMP_STORAGE_DIR, PROCESSED_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Database connection function using .env
def get_db_connection():
    """Establish connection to Neon Database using .env variables"""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT"),
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        logger.error(f"Connection details: host={os.getenv('DB_HOST')}, db={os.getenv('DB_NAME')}, port={os.getenv('DB_PORT')}")
        return None

# SQLAlchemy Engine for pandas operations using .env
def get_sqlalchemy_engine():
    """Create SQLAlchemy engine using .env variables"""
    return create_engine(
        f'postgresql://{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}@{os.getenv("DB_HOST")}:{os.getenv("DB_PORT")}/{os.getenv("DB_NAME")}'
    )

# Function to preprocess the uploaded file
def preprocess_data(file_path, selected_date, log_output):
    """Preprocess the uploaded Excel file, removing the last line if it’s 'Grand Total' in the first column"""
    log_output.info(f"Starting your file…")
    log_output.info(f"Starting preprocessing of file: {os.path.basename(file_path)}")
    
    try:
        df = pd.read_excel(file_path, skiprows=9)
        log_output.info(f"File loaded. Raw shape: {df.shape}")
        
        first_col_name = df.columns[0]
        last_row_first_col = str(df.iloc[-1][first_col_name]).strip().lower()
        if 'grand total' in last_row_first_col:
            df = df.iloc[:-1].copy()
            log_output.info("Removed the last row as it contained 'Grand Total' in the first column")
        else:
            log_output.info("Last row does not contain 'Grand Total' in the first column; proceeding as is")
        
        required_cols = ['Brand', 'Category', 'Size', 'MRP', 'Color', 'SalesQty', 'PurchaseQty']
        if not all(col in df.columns for col in required_cols):
            missing_cols = [col for col in required_cols if col not in df.columns]
            log_output.error(f"Missing required columns: {missing_cols}")
            return None
        
        df = df[required_cols].copy()
        
        for col in ['Brand', 'Category', 'Size', 'Color']:
            df[col] = df[col].str.strip().str.lower()
        
        raw_sales_total = df['SalesQty'].sum()
        raw_purchase_total = df['PurchaseQty'].sum()
        sales_non_zero = (df['SalesQty'].fillna(0) != 0).sum()
        purchase_non_zero = (df['PurchaseQty'].fillna(0) != 0).sum()
        log_output.info(f"Raw totals before cleaning - SalesQty: {int(raw_sales_total)} (non-zero: {sales_non_zero}), PurchaseQty: {int(raw_purchase_total)} (non-zero: {purchase_non_zero})")
        
        for col in ['Brand', 'Category', 'Size', 'Color']:
            df[col] = df[col].fillna('unknown')
        df['MRP'] = df['MRP'].fillna(0.0)
        df['SalesQty'] = pd.to_numeric(df['SalesQty'], errors='coerce').fillna(0).astype(int)
        df['PurchaseQty'] = pd.to_numeric(df['PurchaseQty'], errors='coerce').fillna(0).astype(int)
        
        cleaned_sales_total = df['SalesQty'].sum()
        cleaned_purchase_total = df['PurchaseQty'].sum()
        log_output.info(f"Totals after numeric cleaning - SalesQty: {int(cleaned_sales_total)}, PurchaseQty: {int(cleaned_purchase_total)}")
        
        selected_date_ts = pd.to_datetime(selected_date)
        df['date'] = selected_date_ts
        df['Week'] = df['date'].dt.strftime('%Y-%W')
        df['Month'] = df['date'].dt.strftime('%Y-%m')
        
        df['record_id'] = df.apply(
            lambda x: f"{x['Brand']}_{x['Category']}_{x['Size']}_{x['Color']}_{x['Month']}", 
            axis=1
        )
        log_output.info("Checking for duplicates in uploaded file...")
        before_dedup = len(df)
        
        if df['record_id'].duplicated().any():
            log_output.info(f"Found {df['record_id'].duplicated().sum()} duplicate record_ids to process")
            final_df = df.groupby('record_id').agg({
                'Brand': 'first', 'Category': 'first', 'Size': 'first', 'MRP': 'first',
                'Color': 'first', 'SalesQty': 'sum', 'PurchaseQty': 'sum', 'date': 'first',
                'Week': 'first', 'Month': 'first'
            }).reset_index(drop=True)
            log_output.info(f"After grouping duplicates - SalesQty sum: {int(final_df['SalesQty'].sum())}, PurchaseQty sum: {int(final_df['PurchaseQty'].sum())}")
        else:
            final_df = df.drop('record_id', axis=1)
            log_output.info("No duplicates found")
        
        after_dedup = len(final_df)
        log_output.info(f"Reduced to {after_dedup} unique records from {before_dedup} total rows")
        
        total_sales = int(final_df['SalesQty'].sum())
        total_purchases = int(final_df['PurchaseQty'].sum())
        log_output.info(f"Calculated grand totals - SalesQty: {total_sales}, PurchaseQty: {total_purchases}")
        
        grand_total_row = pd.DataFrame({
            'Brand': ['grand total'], 'Category': [''], 'Size': [''], 'MRP': [0.0], 
            'Color': [''], 'SalesQty': [total_sales], 'PurchaseQty': [total_purchases], 
            'date': [selected_date_ts], 'Week': [selected_date_ts.strftime('%Y-%W')], 
            'Month': [selected_date_ts.strftime('%Y-%m')]
        })
        
        final_df_with_total = pd.concat([grand_total_row, final_df], ignore_index=True)
        
        log_output.info(f"Preprocessing complete with grand total at top. Final shape: {final_df_with_total.shape}")
        return final_df_with_total
    
    except Exception as e:
        log_output.error(f"Error during preprocessing: {str(e)}")
        return None

# Function to save preprocessed file with YYMMDD format
def save_preprocessed_file(df, selected_date, log_output):
    """Save the preprocessed dataframe as Excel file with YYMMDD format"""
    try:
        date_str = selected_date.strftime('%y%m%d')
        file_name = f"salesninventory_{date_str}.xlsx"
        file_path = os.path.join(PROCESSED_DIR, file_name)
        
        with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)

        log_output.info(f"Preprocessed file saved: {file_name}")
        
        df_no_total = df[df['Brand'] != 'grand total'].copy()
        update_master_summary(df_no_total, log_output)
        
        return file_path
    except Exception as e:
        log_output.error(f"Error saving preprocessed file: {str(e)}")
        return None

# Updated function to update master summary
def update_master_summary(new_df, log_output):
    """Update master_summary.xlsx with new data, tracking 30 days, archiving monthly"""
    master_file = os.path.join(PROCESSED_DIR, MASTER_SUMMARY_FILE)
    cutoff_date = pd.Timestamp(datetime.now() - timedelta(days=30))
    current_month = pd.Timestamp.now().strftime('%Y-%m')
    
    try:
        if os.path.exists(master_file):
            master_df = pd.read_excel(master_file)
            master_df['date'] = pd.to_datetime(master_df['date'])
            non_grand_total = master_df[master_df['Brand'] != 'grand total']
            if not non_grand_total.empty:
                first_date = non_grand_total['date'].iloc[0]
                file_month = first_date.strftime('%Y-%m')
                if file_month != current_month:
                    archive_file = os.path.join(PROCESSED_DIR, f"master_summary_{file_month}.xlsx")
                    shutil.move(master_file, archive_file)
                    log_output.info(f"Archived {MASTER_SUMMARY_FILE} to {archive_file}")
                    master_df = pd.DataFrame(columns=new_df.columns)
            else:
                master_df = pd.DataFrame(columns=new_df.columns)
        else:
            master_df = pd.DataFrame(columns=new_df.columns)
        
        master_df = master_df[master_df['Brand'] != 'grand total']
        master_df = master_df[master_df['date'] >= cutoff_date]
        
        combined_df = pd.concat([master_df, new_df], ignore_index=True)
        
        combined_df['record_id'] = combined_df.apply(
            lambda x: f"{x['Brand']}_{x['Category']}_{x['Size']}_{x['Color']}_{x['Month']}", 
            axis=1
        )
        
        final_df = combined_df.groupby('record_id').agg({
            'Brand': 'first', 'Category': 'first', 'Size': 'first', 'MRP': 'first',
            'Color': 'first', 'SalesQty': 'sum', 'PurchaseQty': 'sum', 'date': 'max',
            'Week': 'first', 'Month': 'first'
        }).reset_index(drop=True)
        
        final_df = final_df.sort_values('date', ascending=False)
        
        total_sales = int(final_df['SalesQty'].sum())
        total_purchases = int(final_df['PurchaseQty'].sum())
        grand_total_row = pd.DataFrame({
            'Brand': ['grand total'], 'Category': [''], 'Size': [''], 'MRP': [0.0], 
            'Color': [''], 'SalesQty': [total_sales], 'PurchaseQty': [total_purchases], 
            'date': [pd.Timestamp.now()], 'Week': [pd.Timestamp.now().strftime('%Y-%W')], 
            'Month': [pd.Timestamp.now().strftime('%Y-%m')]
        })
        master_df = pd.concat([grand_total_row, final_df], ignore_index=True)
        
        with pd.ExcelWriter(master_file, engine='xlsxwriter') as writer:
            master_df.to_excel(writer, index=False)

        log_output.info(f"Master summary updated. Rows: {len(master_df)}, Sales: {total_sales}, Purchases: {total_purchases}")
        return True
    
    except Exception as e:
        log_output.error(f"Error updating master summary: {str(e)}")
        return False

# Function to enforce retention policy (keep 7 files)
def enforce_retention_policy(log_output):
    """Keep exactly 7 most recent XLSX files, delete oldest if more than 7"""
    try:
        files = glob.glob(os.path.join(PROCESSED_DIR, "salesninventory_*.xlsx"))
        files.sort()
        
        if len(files) > 7:
            files_to_delete = files[:-7]
            for file in files_to_delete:
                filename = os.path.basename(file)
                if not filename.startswith("salesninventory_") or not filename.endswith(".xlsx"):
                    log_output.warning(f"Skipping invalid filename: {filename}")
                    continue
                prefix_len = len("salesninventory_")
                date_str = filename[prefix_len:prefix_len+6]
                if len(date_str) != 6 or not date_str.isdigit():
                    log_output.warning(f"Skipping file with invalid date format: {filename} (date_str: '{date_str}')")
                    continue
                os.remove(file)
                log_output.info(f"Deleted old file (exceeded 7-file limit): {filename}")
        
        return True
    except Exception as e:
        log_output.error(f"Error enforcing retention policy: {str(e)}")
        return False

# Updated function to upload data to Neon DB with month-specific logic
def upload_to_database(df, selected_date, log_output):
    """Upload preprocessed data to Neon DB, treating first upload of new month as new records"""
    conn = get_db_connection()
    if not conn:
        log_output.error("Failed to connect to database")
        return False
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales_data (
            id SERIAL PRIMARY KEY,
            brand VARCHAR(100),
            category VARCHAR(100),
            size VARCHAR(50),
            mrp FLOAT,
            color VARCHAR(50),
            week VARCHAR(10),
            month VARCHAR(10),
            sales_qty INTEGER,
            purchase_qty INTEGER,
            created_at TIMESTAMP
        )
        """)
        cursor.execute("DROP INDEX IF EXISTS idx_sales_lookup")
        cursor.execute("""
        CREATE INDEX idx_sales_lookup 
        ON sales_data (brand, category, size, color, month)
        """)
        conn.commit()
        
        upload_month = pd.to_datetime(selected_date).strftime('%Y-%m')
        
        cursor.execute("""
        SELECT COUNT(*) 
        FROM sales_data 
        WHERE month = %s AND brand != 'grand total'
        """, (upload_month,))
        month_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM sales_data WHERE brand != 'grand total'")
        total_count = cursor.fetchone()[0]
        
        if total_count == 0:
            log_output.info("First ever upload - inserting all records")
            upload_using_copy(df, selected_date, log_output)
            new_records = len(df[df['Brand'] != 'grand total'])
            updated_records = 0
        elif month_count == 0:
            log_output.info(f"First upload for new month {upload_month} - inserting all records")
            upload_using_copy(df, selected_date, log_output)
            new_records = len(df[df['Brand'] != 'grand total'])
            updated_records = 0
        else:
            log_output.info(f"Updating records for existing month {upload_month}")
            new_records, updated_records = merge_data_with_existing(df, selected_date, log_output)
        
        conn.close()
        update_neon_grand_total(log_output)
        log_output.info(f"Upload complete. Added {new_records} new, updated {updated_records}")
        return {"new": new_records, "updated": updated_records}
    
    except Exception as e:
        log_output.error(f"Database upload error: {str(e)}")
        if conn:
            conn.close()
        return False

# Use COPY command for initial upload with user-defined date
def upload_using_copy(df, selected_date, log_output):
    """Use SQLAlchemy for efficient bulk data upload with user-defined date"""
    try:
        engine = get_sqlalchemy_engine()
        db_df = df[df['Brand'] != 'grand total'][['Brand', 'Category', 'Size', 'MRP', 'Color', 'Week', 'Month', 
                                                  'SalesQty', 'PurchaseQty', 'date']].copy()
        db_df.columns = ['brand', 'category', 'size', 'mrp', 'color', 'week', 'month', 
                         'sales_qty', 'purchase_qty', 'created_at']
        db_df['created_at'] = pd.to_datetime(selected_date)
        
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS sales_data_temp"))
            conn.execute(text("""
                CREATE TEMP TABLE sales_data_temp (
                    brand VARCHAR(100),
                    category VARCHAR(100),
                    size VARCHAR(50),
                    mrp FLOAT,
                    color VARCHAR(50),
                    week VARCHAR(10),
                    month VARCHAR(10),
                    sales_qty INTEGER,
                    purchase_qty INTEGER,
                    created_at TIMESTAMP
                )
            """))
        
        db_df.to_sql('sales_data_temp', engine, if_exists='append', index=False)
        
        with engine.begin() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM sales_data_temp"))
            total_count = result.scalar()
            conn.execute(text("""
                INSERT INTO sales_data 
                (brand, category, size, mrp, color, week, month, sales_qty, purchase_qty, created_at)
                SELECT * FROM sales_data_temp
            """))
            conn.execute(text("DROP TABLE IF EXISTS sales_data_temp"))
        
        log_output.info(f"Inserted {total_count} records into sales_data")
        return {"new": total_count, "updated": 0}
    
    except Exception as e:
        log_output.error(f"Error during bulk upload: {str(e)}")
        return False

# Merge data with existing records
def merge_data_with_existing(df, selected_date, log_output):
    """Merge new data with existing data in the database for the same month, summing quantities"""
    conn = get_db_connection()
    if not conn:
        log_output.error("Failed to connect to database")
        return 0, 0
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
        DROP TABLE IF EXISTS temp_sales_data;
        CREATE TABLE temp_sales_data (
            brand VARCHAR(100),
            category VARCHAR(100),
            size VARCHAR(50),
            mrp FLOAT,
            color VARCHAR(50),
            week VARCHAR(10),
            month VARCHAR(10),
            sales_qty INTEGER,
            purchase_qty INTEGER,
            created_at TIMESTAMP
        )
        """)
        
        df_no_total = df[df['Brand'] != 'grand total'].copy()
        selected_date_ts = pd.to_datetime(selected_date)
        upload_month = selected_date_ts.strftime('%Y-%m')
        temp_data = [
            (row['Brand'], row['Category'], row['Size'], float(row['MRP']), 
             row['Color'], row['Week'], row['Month'], int(row['SalesQty']), 
             int(row['PurchaseQty']), selected_date_ts) for _, row in df_no_total.iterrows()
        ]
        psycopg2.extras.execute_batch(
            cursor,
            """
            INSERT INTO temp_sales_data 
            (brand, category, size, mrp, color, week, month, sales_qty, purchase_qty, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            temp_data,
            page_size=1000
        )
        
        cursor.execute("""
        UPDATE sales_data s
        SET 
            sales_qty = s.sales_qty + t.sales_qty,
            purchase_qty = s.purchase_qty + t.purchase_qty,
            created_at = t.created_at,
            week = t.week,
            month = t.month,
            mrp = t.mrp
        FROM temp_sales_data t
        WHERE s.brand = t.brand AND s.category = t.category AND 
              s.size = t.size AND s.color = t.color AND s.month = t.month
              AND s.month = %s AND s.brand != 'grand total'
        """, (upload_month,))
        updated_records = cursor.rowcount
        log_output.info(f"Updated {updated_records} existing records with summed quantities for month {upload_month}")
        
        cursor.execute("""
        INSERT INTO sales_data 
        (brand, category, size, mrp, color, week, month, sales_qty, purchase_qty, created_at)
        SELECT t.brand, t.category, t.size, t.mrp, t.color, t.week, t.month, 
               t.sales_qty, t.purchase_qty, t.created_at
        FROM temp_sales_data t
        LEFT JOIN sales_data s
        ON s.brand = t.brand AND s.category = t.category AND 
           s.size = t.size AND s.color = t.color AND s.month = t.month
        WHERE s.id IS NULL
        """)
        new_records = cursor.rowcount
        log_output.info(f"Inserted {new_records} new records for month {upload_month}")
        
        cursor.execute("DROP TABLE temp_sales_data")
        conn.commit()
        conn.close()
        
        return new_records, updated_records
    
    except Exception as e:
        log_output.error(f"Error during merge: {str(e)}")
        if conn:
            conn.rollback()
            conn.close()
        return 0, 0

# Clean up Neon DB records older than 3 years
def cleanup_old_db_records(log_output):
    """Remove Neon DB records older than 3 years"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sales_data WHERE created_at < NOW() - INTERVAL '3 years' AND brand != 'grand total'")
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            if deleted > 0:
                log_output.info(f"Deleted {deleted} records older than 3 years from Neon DB")
        except Exception as e:
            log_output.error(f"Error cleaning up Neon DB: {str(e)}")
            conn.close()

# Update Neon DB with grand total
def update_neon_grand_total(log_output):
    """Update Neon DB with a grand total row using current timestamp"""
    conn = get_db_connection()
    if not conn:
        log_output.error("Failed to connect to database for grand total update")
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sales_data WHERE brand = 'grand total'")
        conn.commit()
        
        cursor.execute("""
        SELECT COALESCE(SUM(sales_qty), 0) as total_sales, 
               COALESCE(SUM(purchase_qty), 0) as total_purchases 
        FROM sales_data WHERE brand != 'grand total'
        """)
        result = cursor.fetchone()
        total_sales = int(result[0])
        total_purchases = int(result[1])
        
        current_time = pd.Timestamp.now()
        cursor.execute("""
        INSERT INTO sales_data (brand, category, size, mrp, color, week, month, sales_qty, purchase_qty, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, ('grand total', '', '', 0.0, '', current_time.strftime('%Y-%W'), 
              current_time.strftime('%Y-%m'), total_sales, total_purchases, 
              current_time))
        
        conn.commit()
        conn.close()
        log_output.info(f"Updated Neon DB with grand total: Sales={total_sales}, Purchases={total_purchases}, Timestamp={current_time}")
    except Exception as e:
        log_output.error(f"Error updating Neon DB grand total: {str(e)}")
        if conn:
            conn.rollback()
            conn.close()

# Get data from Neon DB for preview
def get_database_preview(log_output):
    """Get latest 1000 records from Neon DB, ensuring Grand Total is first"""
    try:
        engine = get_sqlalchemy_engine()
        query = """
        SELECT * FROM sales_data 
        ORDER BY CASE WHEN brand = 'grand total' THEN 0 ELSE 1 END, created_at DESC 
        LIMIT 1000
        """
        df = pd.read_sql(query, engine)
        log_output.info(f"Retrieved {len(df)} latest records from Neon DB")
        return df
    except Exception as e:
        log_output.error(f"Error getting preview: {str(e)}")
        return pd.DataFrame()
#local preview
def clean_json(data):
    if isinstance(data, dict):
        return {k: clean_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_json(i) for i in data]
    elif isinstance(data, (datetime, pd.Timestamp)):
        return data.isoformat()
    elif pd.isna(data):
        return None
    elif isinstance(data, (np.integer, np.floating)):
        return data.item()
    return data

def get_data_preview():
    preview = {"daily_files": {"latest_files_info": [], "file_count": 0}, "master_summary": {}}
    try:
        files = sorted(glob.glob(os.path.join(PROCESSED_DIR, "salesninventory_*.xlsx")), reverse=True)
        latest_files = files[:7]
        preview["daily_files"]["file_count"] = len(latest_files)

        for file_path in latest_files:
            file_name = os.path.basename(file_path)
            try:
                df = pd.read_excel(file_path)
                df = df.fillna("")
                for col in ['SalesQty', 'PurchaseQty', 'MRP']:
                    if col in df.columns:
                        df[col] = df[col].astype(float).round(2).astype(str)
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
                
                df_no_total = df[df['Brand'] != 'grand total']
                stats = {
                    "total_sales": int(df_no_total['SalesQty'].astype(float).sum()),
                    "total_purchases": int(df_no_total['PurchaseQty'].astype(float).sum()),
                    "unique_brands": df_no_total['Brand'].nunique(),
                    "unique_categories": df_no_total['Category'].nunique()
                }
                ctime = datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
                
                file_info = {
                    "file": file_name, "rows": len(df), "columns": df.columns.tolist(),
                    "grand_total_date": df.iloc[0]["date"] if "date" in df.columns and not df.empty else "",
                    "sample": df.head(10).to_dict(orient="records"), "stats": stats, "created_at": ctime
                }
                preview["daily_files"]["latest_files_info"].append(file_info)
                logger.info(f"Processed {file_name}")
            except Exception as e:
                logger.error(f"Error processing {file_name}: {str(e)}")
                continue

        master_path = os.path.join(PROCESSED_DIR, "master_summary.xlsx")
        if os.path.exists(master_path):
            try:
                mdf = pd.read_excel(master_path)
                mdf = mdf.fillna("")
                for col in ['SalesQty', 'PurchaseQty', 'MRP']:
                    if col in mdf.columns:
                        mdf[col] = mdf[col].astype(float).round(2).astype(str)
                if 'date' in mdf.columns:
                    mdf['date'] = pd.to_datetime(mdf['date']).dt.strftime('%Y-%m-%d')
                
                mdf_no_total = mdf[mdf['Brand'] != 'grand total']
                stats = {
                    "total_sales": int(mdf_no_total['SalesQty'].astype(float).sum()),
                    "total_purchases": int(mdf_no_total['PurchaseQty'].astype(float).sum()),
                    "unique_brands": mdf_no_total['Brand'].nunique(),
                    "unique_categories": mdf_no_total['Category'].nunique()
                }
                ctime = datetime.fromtimestamp(os.path.getctime(master_path)).isoformat()
                
                preview["master_summary"] = {
                    "status": "available", "columns": mdf.columns.tolist(), "row_count": len(mdf),
                    "grand_total_date": mdf.iloc[0]["date"] if "date" in mdf.columns and not mdf.empty else "",
                    "sample": mdf.head(10).to_dict(orient="records"), "stats": stats, "created_at": ctime
                }
                logger.info("Processed master_summary.xlsx")
            except Exception as e:
                logger.error(f"Error processing master_summary.xlsx: {str(e)}")
                preview["master_summary"]["status"] = "error"
                preview["master_summary"]["error"] = str(e)
        else:
            preview["master_summary"]["status"] = "missing"
            logger.warning("master_summary.xlsx not found")

        return clean_json(preview)
    except Exception as e:
        logger.error(f"Error in get_data_preview: {str(e)}")
        return {"error": str(e)}
    
# Get aggregated data for visualizations with date filters
def get_visualization_data(log_output, start_date=None, end_date=None):
    """Get aggregated data from Neon DB with optional date range"""
    try:
        engine = get_sqlalchemy_engine()
        where_clause = "WHERE created_at BETWEEN %s AND %s AND brand != 'grand total'" if start_date and end_date else "WHERE brand != 'grand total'"
        params = (start_date, end_date) if start_date and end_date else ()
        
        brand_query = f"""
        SELECT brand, SUM(sales_qty) as total_sales, SUM(purchase_qty) as total_purchases
        FROM sales_data {where_clause}
        GROUP BY brand ORDER BY total_sales DESC LIMIT 10
        """
        brand_df = pd.read_sql(brand_query, engine, params=params)
        
        category_query = f"""
        SELECT category, SUM(sales_qty) as total_sales, SUM(purchase_qty) as total_purchases
        FROM sales_data {where_clause}
        GROUP BY category ORDER BY total_sales DESC LIMIT 10
        """
        category_df = pd.read_sql(category_query, engine, params=params)
        
        monthly_query = f"""
        SELECT month, SUM(sales_qty) as total_sales, SUM(purchase_qty) as total_purchases
        FROM sales_data {where_clause}
        GROUP BY month ORDER BY month
        """
        monthly_df = pd.read_sql(monthly_query, engine, params=params)
        
        weekly_query = f"""
        SELECT week, SUM(sales_qty) as total_sales, SUM(purchase_qty) as total_purchases
        FROM sales_data {where_clause}
        GROUP BY week ORDER BY week
        """
        weekly_df = pd.read_sql(weekly_query, engine, params=params)
        
        log_output.info("Retrieved aggregated data for visualizations")
        return {"brand": brand_df, "category": category_df, "monthly": monthly_df, "weekly": weekly_df}
    except Exception as e:
        log_output.error(f"Error getting viz data: {str(e)}")
        return {}

# Helper function to convert NumPy arrays to lists recursively
def convert_numpy_to_list(obj):
    """Recursively convert NumPy arrays to Python lists in a dictionary"""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_to_list(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_to_list(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    return obj

def create_visualizations(data):
    """Create visualizations using Plotly Graph Objects with a single trace per chart"""
    visualizations = {}
    
    if not data:
        return visualizations
    
    # Top 10 Brands (Stacked Bar Chart)
    if "brand" in data and not data["brand"].empty:
        brand_fig = go.Figure()
        brand_fig.add_trace(go.Bar(
            x=data["brand"]["brand"],
            y=data["brand"]["total_sales"],
            name="Total Sales",
            marker_color="#00CC96"
        ))
        brand_fig.add_trace(go.Bar(
            x=data["brand"]["brand"],
            y=data["brand"]["total_purchases"],
            name="Total Purchases",
            marker_color="#EF553B"
        ))
        brand_fig.update_layout(
            title="Top 10 Brands by Sales and Purchases",
            barmode="stack",
            xaxis_title="Brand",
            yaxis_title="Quantity"
        )
        visualizations["brand"] = json.dumps({
            "data": [convert_numpy_to_list(trace.to_plotly_json()) for trace in brand_fig.data],
            "layout": convert_numpy_to_list(brand_fig.layout.to_plotly_json())
        })
    
    # Top 10 Categories (Stacked Bar Chart)
    if "category" in data and not data["category"].empty:
        category_fig = go.Figure()
        category_fig.add_trace(go.Bar(
            x=data["category"]["category"],
            y=data["category"]["total_sales"],
            name="Total Sales",
            marker_color="#00CC96"
        ))
        category_fig.add_trace(go.Bar(
            x=data["category"]["category"],
            y=data["category"]["total_purchases"],
            name="Total Purchases",
            marker_color="#EF553B"
        ))
        category_fig.update_layout(
            title="Top 10 Categories by Sales and Purchases",
            barmode="stack",
            xaxis_title="Category",
            yaxis_title="Quantity"
        )
        visualizations["category"] = json.dumps({
            "data": [convert_numpy_to_list(trace.to_plotly_json()) for trace in category_fig.data],
            "layout": convert_numpy_to_list(category_fig.layout.to_plotly_json())
        })
    
    # Monthly Trends (Single Line Chart with Combined Values)
    if "monthly" in data and not data["monthly"].empty:
        monthly_fig = go.Figure()
        monthly_fig.add_trace(go.Scatter(
            x=data["monthly"]["month"],
            y=data["monthly"]["total_sales"] + data["monthly"]["total_purchases"],
            mode="lines+markers",
            name="Total Sales + Purchases",
            line=dict(color="#00CC96")
        ))
        monthly_fig.update_layout(
            title="Monthly Sales and Purchase Trends",
            xaxis_title="Month",
            yaxis_title="Total Quantity"
        )
        visualizations["monthly"] = json.dumps({
            "data": [convert_numpy_to_list(trace.to_plotly_json()) for trace in monthly_fig.data],
            "layout": convert_numpy_to_list(monthly_fig.layout.to_plotly_json())
        })
    
    # Weekly Trends (Single Line Chart with Combined Values)
    if "weekly" in data and not data["weekly"].empty:
        weekly_fig = go.Figure()
        weekly_fig.add_trace(go.Scatter(
            x=data["weekly"]["week"],
            y=data["weekly"]["total_sales"] + data["weekly"]["total_purchases"],
            mode="lines+markers",
            name="Total Sales + Purchases",
            line=dict(color="#00CC96")
        ))
        weekly_fig.update_layout(
            title="Weekly Sales and Purchase Trends",
            xaxis_title="Week",
            yaxis_title="Total Quantity"
        )
        visualizations["weekly"] = json.dumps({
            "data": [convert_numpy_to_list(trace.to_plotly_json()) for trace in weekly_fig.data],
            "layout": convert_numpy_to_list(weekly_fig.layout.to_plotly_json())
        })
    
    return visualizations

# Custom logger for Flask
class FlaskLogger:
    def __init__(self):
        self.logs = []
    
    def info(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[INFO] {timestamp} - {message}"
        self.logs.append(log_entry)
        logger.info(message)
    
    def error(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[ERROR] {timestamp} - {message}"
        self.logs.append(log_entry)
        logger.error(message)
    
    def warning(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[WARNING] {timestamp} - {message}"
        self.logs.append(log_entry)
        logger.warning(message)
    
    def get_logs(self):
        return self.logs[-20:]  # Return last 20 logs

# Flask Routes
@app.route('/')
def serve_index():
    return render_template('other.html')

@app.route('/process', methods=['POST'])
def process_data():
    log_output = FlaskLogger()
    if 'file' not in request.files or 'date' not in request.form:
        log_output.error("No file or date provided")
        return jsonify({"error": "No file or date provided", "logs": log_output.get_logs()}), 400
    
    file = request.files['file']
    selected_date = pd.to_datetime(request.form['date'])
    
    if file.filename == '':
        log_output.error("No file selected")
        return jsonify({"error": "No file selected", "logs": log_output.get_logs()}), 400
    
    log_output.info("Starting file processing...")
    temp_file_path = os.path.join(TEMP_STORAGE_DIR, file.filename)
    file.save(temp_file_path)
    log_output.info(f"File saved temporarily: {file.filename}")
    
    df = preprocess_data(temp_file_path, selected_date, log_output)
    if df is None:
        os.remove(temp_file_path)
        return jsonify({"error": "Failed to preprocess data", "logs": log_output.get_logs()}), 500
    
    preprocessed_path = save_preprocessed_file(df, selected_date, log_output)
    if not preprocessed_path:
        os.remove(temp_file_path)
        return jsonify({"error": "Failed to save preprocessed file", "logs": log_output.get_logs()}), 500
    
    enforce_retention_policy(log_output)
    results = upload_to_database(df, selected_date, log_output)
    os.remove(temp_file_path)
    
    if not results:
        return jsonify({"error": "Failed to upload data to database", "logs": log_output.get_logs()}), 500
    
    master_file = os.path.join(PROCESSED_DIR, MASTER_SUMMARY_FILE)
    if os.path.exists(master_file):
        master_df = pd.read_excel(master_file)
        grand_total_row = master_df[master_df['Brand'] == 'grand total'].iloc[0]
        local_total_sales = int(grand_total_row['SalesQty'])
        local_total_purchases = int(grand_total_row['PurchaseQty'])
    else:
        local_total_sales, local_total_purchases = 0, 0
    
    date_str = selected_date.strftime('%y%m%d')
    file_name = f"salesninventory_{date_str}.xlsx"
    file_path = os.path.join(PROCESSED_DIR, file_name)
    if os.path.exists(file_path):
        daily_df = pd.read_excel(file_path)
        daily_grand_row = daily_df[daily_df['Brand'] == 'grand total'].iloc[0]
        daily_total_sales = int(daily_grand_row['SalesQty'])
        daily_total_purchases = int(daily_grand_row['PurchaseQty'])
    else:
        daily_total_sales, daily_total_purchases = 0, 0
    
    response = {
        "status": "success",
        "results": {
            "new_records": results["new"],
            "updated_records": results["updated"],
            "total_records": len(df),
            "date": selected_date.strftime("%Y-%m-%d"),
            "daily_total_sales": daily_total_sales,
            "daily_total_purchases": daily_total_purchases,
            "master_total_sales": local_total_sales,
            "master_total_purchases": local_total_purchases,
            "file_name": file_name
        },
        "logs": log_output.get_logs()
    }
    log_output.info("Data pipeline process completed successfully!")
    return jsonify(response)

@app.route('/download/<file_name>', methods=['GET'])
def download_file(file_name):
    file_path = os.path.join(PROCESSED_DIR, file_name)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=file_name)
    return jsonify({"error": "File not found"}), 404

@app.route('/preview', methods=['GET'])
def get_preview():
    log_output = FlaskLogger()
    preview_df = get_database_preview(log_output)
    
    if preview_df.empty:
        return jsonify({
            "warning": "No data available in the database",
            "data": [],
            "metrics": {
                "total_records": 0,
                "unique_brands": 0,
                "unique_categories": 0,
                "neon_total_sales": 0,
                "neon_total_purchases": 0
            },
            "logs": log_output.get_logs()
        })
    
    # Fetch the grand total row for metrics
    grand_total_row = preview_df[preview_df['brand'] == 'grand total']
    if grand_total_row.empty:
        neon_total_sales = 0
        neon_total_purchases = 0
    else:
               neon_total_sales = int(grand_total_row.iloc[0]['sales_qty'])
               neon_total_purchases = int(grand_total_row.iloc[0]['purchase_qty'])
    
    # Prepare the preview data (excluding grand total for the table)
    preview_data = preview_df.to_dict(orient='records')
    
    # Calculate metrics
    df_no_grand = preview_df[preview_df['brand'] != 'grand total']
    response = {
        "data": preview_data,
        "metrics": {
            "total_records": len(df_no_grand),
            "unique_brands": df_no_grand['brand'].nunique(),
            "unique_categories": df_no_grand['category'].nunique(),
            "neon_total_sales": neon_total_sales,
            "neon_total_purchases": neon_total_purchases
        },
        "logs": log_output.get_logs()
    }
    return jsonify(response)

@app.route('/grand-total', methods=['GET'])
def get_grand_total():
    log_output = FlaskLogger()
    preview_df = get_database_preview(log_output)
    
    if preview_df.empty:
        return jsonify({
            "warning": "No data available in the database",
            "grand_total_sales": 0,
            "grand_total_purchases": 0,
            "logs": log_output.get_logs()
        })
    
    # Fetch the grand total row
    grand_total_row = preview_df[preview_df['brand'] == 'grand total']
    if grand_total_row.empty:
        # If no grand total row exists, calculate totals manually
        df_no_grand = preview_df[preview_df['brand'] != 'grand total']
        grand_total_sales = int(df_no_grand['sales_qty'].sum())
        grand_total_purchases = int(df_no_grand['purchase_qty'].sum())
        log_output.warning("Grand total row not found in the database; calculated totals manually")
    else:
        grand_total_sales = int(grand_total_row.iloc[0]['sales_qty'])
        grand_total_purchases = int(grand_total_row.iloc[0]['purchase_qty'])
    
    response = {
        "grand_total_sales": grand_total_sales,
        "grand_total_purchases": grand_total_purchases,
        "logs": log_output.get_logs()
    }
    return jsonify(response)

@app.route('/visualizations', methods=['GET', 'POST'])
def get_visualizations():
    log_output = FlaskLogger()
    
    # Handle date filters
    if request.method == 'POST':
        data = request.get_json()
        start_date = pd.to_datetime(data.get('start_date')) if data.get('start_date') else None
        end_date = pd.to_datetime(data.get('end_date')) if data.get('end_date') else None
    else:  # GET request
        start_date = None
        end_date = None
    
    # Fetch visualization data using the existing get_visualization_data function
    viz_data = get_visualization_data(log_output, start_date, end_date)
    if not viz_data:
        return jsonify({"warning": "No data available for visualizations", "logs": log_output.get_logs()})
    
    # Generate visualizations
    visualizations = create_visualizations(viz_data)
    return jsonify({"visualizations": visualizations, "logs": log_output.get_logs()})

# Register the chatbot route from chatbot.py
@app.route('/chatbot', methods=['POST'])
def chat_with_bot():
    data = request.get_json()
    question = data.get("question", "")
    
    if not question:
        return jsonify({"error": "No question provided"}), 400

    response_text = chatbot.process_user_question(question)
    return jsonify({"message": response_text}) 

@app.route("/local-files")
def serve_local_file_data():
    try:
        preview = get_data_preview()
        return jsonify(preview)
    except Exception as e:
        logger.error(f"Error serving local files: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/delete/<file_name>', methods=['DELETE'])
def delete_file(file_name):
    file_path = os.path.join(PROCESSED_DIR, file_name)
    if file_name == 'master_summary.xlsx':
        return jsonify({"error": "Cannot delete master summary"}), 403
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            logger.info(f"Deleted {file_name}")
            return jsonify({"status": "success", "message": f"Deleted {file_name}"})
        except Exception as e:
            logger.error(f"Error deleting {file_name}: {str(e)}")
            return jsonify({"error": str(e)}), 500
    return jsonify({"error": "File not found"}), 404

@app.route('/download-zip', methods=['GET'])
def download_zip():
    try:
        memory_file = BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in glob.glob(os.path.join(PROCESSED_DIR, "salesninventory_*.xlsx")):
                zf.write(file_path, os.path.basename(file_path))
        memory_file.seek(0)
        logger.info("Generated ZIP archive")
        return send_file(memory_file, mimetype='application/zip', as_attachment=True, download_name='daily_files.zip')
    except Exception as e:
        logger.error(f"Error creating ZIP: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
