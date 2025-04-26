import os
import pandas as pd
import sqlite3
import tempfile
import psycopg2
import datetime
import glob
import re
import json
import sys
import time
from typing import Dict, List, Any, Optional, Union
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("Warning: GEMINI_API_KEY not found in environment variables. Please set it.")
    API_KEY = ""  # Placeholder, will fail if not replaced

genai.configure(api_key=API_KEY)

# Initialize Gemini model
model = genai.GenerativeModel('gemini-2.0-flash')

class SalesDataChatbot:
    def __init__(self):
        self.temp_db_path = None
        self.conn = None
        self.cursor = None
        self.neon_conn_string = os.getenv("NEON_DB_CONNECTION_STRING")
        self.processed_data_dir = "processed_data"
        self.data_sources = {}
        self.available_tables = []
        self.grand_total_dates = {}  # Store grand total dates for each data source
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def finalize(self):
        """Manually trigger cleanup after response is sent"""
        self.cleanup()
    
    def cleanup(self):
        """Clean up temporary resources"""
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
            
        if self.temp_db_path and os.path.exists(self.temp_db_path):
            try:
                os.remove(self.temp_db_path)
                print(f"Temporary database removed: {self.temp_db_path}")
            except Exception as e:
                print(f"Warning: Could not remove temporary database: {e}")
    
    def test_neon_connection(self) -> Dict[str, Any]:
        """Test connection to Neon DB and return status"""
        if not self.neon_conn_string:
            return {
                "status": "unavailable",
                "error": "NEON_DB_CONNECTION_STRING not set in environment variables"
            }
            
        try:
            with psycopg2.connect(self.neon_conn_string) as conn:
                with conn.cursor() as cursor:
                    # Check if sales_data table exists
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = 'sales_data'
                        );
                    """)
                    table_exists = cursor.fetchone()[0]
                    
                    if not table_exists:
                        return {
                            "status": "unavailable",
                            "error": "sales_data table does not exist in the database"
                        }
                    
                    # Get sample data and columns
                    cursor.execute("SELECT * FROM sales_data LIMIT 5")
                    columns = [desc[0] for desc in cursor.description]
                    data = cursor.fetchall()
                    
                    return {
                        "status": "available",
                        "columns": columns,
                        "sample": data,
                        "description": "Historical sales data for the past 3 years"
                    }
        except Exception as e:
            return {
                "status": "unavailable",
                "error": str(e)
            }
    
    def find_excel_files(self) -> Dict[str, Dict[str, Any]]:
        """Find and validate Excel files in the processed_data directory"""
        result = {}
        
        # Ensure the directory exists
        if not os.path.exists(self.processed_data_dir):
            os.makedirs(self.processed_data_dir)
            print(f"Created directory: {self.processed_data_dir}")
            return {
                "master_summary": {"status": "unavailable", "error": "Directory was empty, created it"},
                "daily_files": {"status": "unavailable", "error": "Directory was empty, created it"}
            }
        
        # Check for master_summary.xlsx
        master_summary_path = os.path.join(self.processed_data_dir, "master_summary.xlsx")
        if os.path.exists(master_summary_path):
            try:
                df = pd.read_excel(master_summary_path)
                
                # Extract grand total date
                grand_total_row = df[df['Brand'].str.lower() == 'grand total'].iloc[0] if any(df['Brand'].str.lower() == 'grand total') else None
                grand_total_date = grand_total_row['date'] if grand_total_row is not None else None
                
                # Store grand total date for future reference
                if grand_total_date:
                    self.grand_total_dates["master_summary"] = grand_total_date
                
                result["master_summary"] = {
                    "status": "available",
                    "path": master_summary_path,
                    "columns": list(df.columns),
                    "row_count": len(df),
                    "sample": df.head(5).to_dict('records'),
                    "grand_total_date": grand_total_date,
                    "description": "Aggregated current-month business data"
                }
            except Exception as e:
                result["master_summary"] = {
                    "status": "unavailable",
                    "path": master_summary_path,
                    "error": str(e)
                }
        else:
            result["master_summary"] = {
                "status": "unavailable",
                "error": f"File not found: {master_summary_path}"
            }
        
        # Find daily sales files (salesninventory_YYMMDD.xlsx)
        daily_files = glob.glob(os.path.join(self.processed_data_dir, "salesninventory_*.xlsx"))
        if daily_files:
            # Sort by filename which should reflect date
            daily_files.sort(reverse=True)
            
            daily_files_info = []
            for file_path in daily_files[:5]:  # Process only the 5 most recent for info
                try:
                    file_name = os.path.basename(file_path)
                    df = pd.read_excel(file_path)
                    
                    # Extract grand total date
                    grand_total_row = df[df['Brand'].str.lower() == 'grand total'].iloc[0] if any(df['Brand'].str.lower() == 'grand total') else None
                    grand_total_date = grand_total_row['date'] if grand_total_row is not None else None
                    
                    # Store grand total date for future reference
                    if grand_total_date:
                        self.grand_total_dates[file_name] = grand_total_date
                    
                    daily_files_info.append({
                        "file": file_name,
                        "path": file_path,
                        "rows": len(df),
                        "columns": list(df.columns),
                        "grand_total_date": grand_total_date
                    })
                except Exception as e:
                    daily_files_info.append({
                        "file": os.path.basename(file_path),
                        "path": file_path,
                        "error": str(e)
                    })
            
            # Only store info for the first few files to keep the data size manageable
            result["daily_files"] = {
                "status": "available",
                "files": [os.path.basename(f) for f in daily_files],
                "file_count": len(daily_files),
                "latest_files_info": daily_files_info,
                "description": "Daily preprocessed sales and inventory data"
            }
        else:
            result["daily_files"] = {
                "status": "unavailable",
                "error": "No salesninventory_*.xlsx files found"
            }
            
        return result
    
    def get_data_preview(self) -> Dict[str, Dict[str, Any]]:
        """Generate a preview of all available data sources"""
        # Store the data sources for later use
        self.data_sources = {
            "sales_data": self.test_neon_connection(),
            **self.find_excel_files()
        }
        
        # Filter out sensitive info for the preview
        filtered_preview = {}
        for source, data in self.data_sources.items():
            filtered_copy = data.copy()
            # Remove connection strings or paths
            if "path" in filtered_copy:
                del filtered_copy["path"]
            filtered_preview[source] = filtered_copy
            
        return filtered_preview
    
    def create_temp_sqlite_db(self, file_paths: List[str]) -> sqlite3.Connection:
        """Create a temporary SQLite database from Excel files"""
        # Clean up any existing connection
        if self.conn:
            self.conn.close()
            self.conn = None
            
        if self.temp_db_path and os.path.exists(self.temp_db_path):
            try:
                os.remove(self.temp_db_path)
            except Exception:
                pass
        
        # Create a temporary file with a recognizable name
        temp_dir = tempfile.gettempdir()
        self.temp_db_path = os.path.join(temp_dir, f"sales_data_{int(time.time())}.db")
        
        # Connect to the SQLite database
        self.conn = sqlite3.connect(self.temp_db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        
        # Track the tables we create
        self.available_tables = []
        
        # Process each file
        for file_path in file_paths:
            try:
                file_name = os.path.basename(file_path)
                
                # Determine table name (remove extension and make SQL-safe)
                if "master_summary" in file_name.lower():
                    table_name = "master_summary"
                else:
                    # Extract the date from the filename
                    match = re.search(r'salesninventory_(\d+)\.xlsx', file_name, re.IGNORECASE)
                    if match:
                        date_part = match.group(1)
                        table_name = f"daily_{date_part}"
                    else:
                        # Fallback to a generic name
                        table_name = file_name.replace('.xlsx', '').lower()
                        table_name = re.sub(r'[^a-z0-9_]', '_', table_name)
                
                # Read Excel file
                print(f"Loading {file_path} into SQLite table '{table_name}'...")
                df = pd.read_excel(file_path)
                
                # Convert column names to lowercase with underscores for consistency
                df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', col).lower() for col in df.columns]
                
                # Add a file_source column to identify the source
                df['file_source'] = file_name
                
                # Write to SQLite
                df.to_sql(table_name, self.conn, if_exists='replace', index=False)
                self.available_tables.append(table_name)
                
                print(f"Created table '{table_name}' with {len(df)} rows and {len(df.columns)} columns")
                
                # Create a separate view without the grand total row
                try:
                    view_name = f"{table_name}_no_grand_total"
                    self.cursor.execute(f"""
                        CREATE VIEW {view_name} AS
                        SELECT * FROM {table_name}
                        WHERE lower(brand) != 'grand total'
                    """)
                    self.available_tables.append(view_name)
                    print(f"Created view '{view_name}' excluding grand total rows")
                except Exception as e:
                    print(f"Error creating view {view_name}: {e}")
                
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
        
        # Create a special table to store grand total dates
        try:
            grand_total_dates_df = pd.DataFrame(
                [{"source": k, "grand_total_date": v} for k, v in self.grand_total_dates.items()]
            )
            grand_total_dates_df.to_sql("grand_total_dates", self.conn, if_exists='replace', index=False)
            self.available_tables.append("grand_total_dates")
            print(f"Created table 'grand_total_dates' with {len(grand_total_dates_df)} rows")
        except Exception as e:
            print(f"Error creating grand_total_dates table: {e}")
        
        return self.conn
    
    def execute_neon_query(self, query: str) -> Union[List[Dict[str, Any]], Dict[str, str]]:
        """Execute a query on the Neon database"""
        try:
            with psycopg2.connect(self.neon_conn_string) as conn:
                with conn.cursor() as cursor:
                    print(f"Executing on Neon DB: {query}")
                    cursor.execute(query)
                    
                    # Check if this is a SELECT query
                    if cursor.description:
                        columns = [desc[0] for desc in cursor.description]
                        data = cursor.fetchall()
                        
                        # Convert to list of dictionaries for easier processing
                        result = []
                        for row in data:
                            result.append(dict(zip(columns, row)))
                        
                        return result
                    else:
                        # For non-SELECT queries
                        return {"message": f"Query executed successfully. {cursor.rowcount} rows affected."}
        except Exception as e:
            error_msg = str(e)
            print(f"Neon DB Error: {error_msg}")
            return {"error": f"Database query error: {error_msg}"}
    
    def execute_sqlite_query(self, query: str) -> Union[List[Dict[str, Any]], Dict[str, str]]:
        """Execute a query on the temporary SQLite database"""
        try:
            if not self.conn:
                return {"error": "No active SQLite connection"}
            
            # Print the list of available tables
            print(f"Available SQLite tables: {', '.join(self.available_tables)}")
            print(f"Executing on SQLite: {query}")
            
            cursor = self.conn.cursor()
            cursor.execute(query)
            
            # Check if this is a SELECT query
            if cursor.description:
                columns = [description[0] for description in cursor.description]
                data = cursor.fetchall()
                
                # Convert to list of dictionaries for easier processing
                result = []
                for row in data:
                    row_dict = {}
                    for i, value in enumerate(row):
                        # Handle datetime objects and other non-JSON serializable types
                        if isinstance(value, (datetime.datetime, datetime.date)):
                            row_dict[columns[i]] = value.isoformat()
                        else:
                            row_dict[columns[i]] = value
                    result.append(row_dict)
                
                return result
            else:
                # For non-SELECT queries
                return {"message": f"Query executed successfully. {cursor.rowcount} rows affected."}
        except Exception as e:
            error_msg = str(e)
            print(f"SQLite Error: {error_msg}")
            return {"error": f"SQLite query error: {error_msg}"}
    
    def prepare_data_sources(self) -> None:
        """Prepare all data sources for querying"""
        # Get data sources info
        preview = self.get_data_preview()
        
        # If local files are available, prepare the SQLite database
        local_files = []
        
        # Add master summary if available
        if self.data_sources.get("master_summary", {}).get("status") == "available":
            local_files.append(self.data_sources["master_summary"]["path"])
        
        # Add daily files if available (don't combine them)
        if self.data_sources.get("daily_files", {}).get("status") == "available":
            daily_files_info = self.data_sources["daily_files"]
            for file_name in daily_files_info.get("files", []):
                file_path = os.path.join(self.processed_data_dir, file_name)
                if os.path.exists(file_path):
                    local_files.append(file_path)
        
        # Create SQLite database if we have local files
        if local_files:
            self.create_temp_sqlite_db(local_files)
    
    def process_user_question(self, question: str) -> str:
        """Process a user question and generate a response"""
        try:
            print(f"Processing question: {question}")
            
            # Prepare all data sources
            self.prepare_data_sources()
            
            # Get data preview
            data_preview = self.get_data_preview()
            
            # Generate a detailed system prompt
            system_prompt = """
            You are an AI assistant specializing in sales data analysis. Your task is to:
            1. Analyze the user's question to understand what data and calculations are needed
            2. Determine the best data source for the question
            3. Generate appropriate SQL queries to extract the required data
            4. Format the information into a clear, natural language response using Markdown

            When analyzing questions about inventory, sales velocity, and projections:
            - "Sales velocity" refers to the rate at which products are selling
            - To calculate days until sold out: (Current Inventory) / (Average Daily Sales)
            - For percentage sold: (SalesQty / PurchaseQty) * 100
            - IMPORTANT: ALWAYS exclude "grand total" rows in your queries with a WHERE clause like "WHERE lower(brand) != 'grand total'"
            - Use the date from the grand total row as a baseline for time calculations

            If the required data seems missing, try to derive it from available data or suggest alternatives.
            """
            
            # Create a detailed schema description
            schema_description = """
            DATA SOURCES OVERVIEW:

            1. NEON DATABASE (Historical Data - 3 years)
               - Table: sales_data
               - Contains historical aggregated data by month/week
               - Key fields: brand, category, color, size, mrp, month, week, purchase_qty, sales_qty, created_at
               - Notes: Use month/week for time analysis, not created_at
               - IMPORTANT: Records older than 3 years are purged

            2. MASTER SUMMARY FILE (Current Month Data)
               - Table: master_summary
               - Contains aggregated data for the current month
               - Key fields: brand, category, color, size, mrp, month, week, purchase_qty, sales_qty, date
               - IMPORTANT: Excludes grand total row in "master_summary_no_grand_total" view
               - The "date" field represents when records were last updated
               - Grand total dates are available in the "grand_total_dates" table

            3. DAILY FILES (Daily Data)
               - Tables: daily_YYMMDD (one table per file)
               - Contains daily sales and inventory snapshots
               - Key fields: Same as master_summary
               - Notes: The "date" field represents the upload day for each file
               - IMPORTANT: Each daily_YYMMDD has a corresponding daily_YYMMDD_no_grand_total view

            SPECIAL CONSIDERATIONS:
            - "Grand total" rows must ALWAYS be excluded from direct analysis
            - For calculations needing the grand total date, reference the grand_total_dates table
            - Each data source has a different purpose and time range
            - Column names in SQLite tables use lowercase with underscores
            - mrp/MRP in rupees and not dollar.
            """
            
            # Additional analytics guidance
            analytics_guidance = """
            ANALYTICS GUIDANCE:

            1. For historical trends or year-over-year analysis:
               - Use Neon DB (sales_data table)
               - Group by appropriate time periods (month/week)

            2. For current month analysis or recent aggregated data:
               - Use master_summary_no_grand_total view
               - Use the grand_total_date for time-based calculations

            3. For very recent daily trends or daily inventory status:
               - Use the appropriate daily_YYMMDD_no_grand_total view
               - For the most recent data, use the latest daily table

            4. For sales velocity and projection calculations:
               - Current velocity = Recent SalesQty / Number of days in period
               - Estimated days to sell out = Current Inventory / Daily sales velocity
                 where Current Inventory = (PurchaseQty - SalesQty)
               - Percentage sold = (SalesQty / PurchaseQty) * 100

            5. When SQL syntax differs between Neon (PostgreSQL) and SQLite:
               - For date functions, adjust accordingly
               - For string operations, use lower() in both systems

            6. IMPORTANT FORMATTING REQUIREMENTS:
               - Format all responses in Markdown for readability
               - Use headings, bullet points, and tables appropriately
               - For numeric values, use proper formatting (e.g., percentages, currency)
               - Highlight important findings or items that need attention
            
               7. For unrealistic data or answers:-
                - If the answer contains unrealistic data then use other data that is available for getting answer that is realistic.
                - Make sure no inf, negative values where not needed are generated as answers.
            """
            
            # Include actual data source details
            data_source_details = json.dumps(data_preview, indent=2, default=str)
            
            # Generate the decision analysis
            decision_prompt = f"""
            You are an expert data analyst AI assistant that generates SQL queries based on user questions. You have access to multiple data sources, including a PostgreSQL database and multiple SQLite tables created from Excel files.

            ## YOUR MISSION:
            Analyze the user question and generate an SQL query that extracts the required data **with perfect syntax compatibility** for either SQLite (for local Excel-based data) or PostgreSQL (for Neon DB).

            ---

            ## WHAT YOU MUST DO:
            1. **Understand the user's business question** — sales trends, inventory, velocity, projections, etc.
            2. **Choose the best available data source**:
            - Use `sales_data` (Postgres) for historical/monthly/yearly data
            - Use `master_summary_no_grand_total` (SQLite) for current month data
            - Use `daily_YYMMDD_no_grand_total` (SQLite) for recent daily snapshots
            3. **Generate a clean, compatible SQL query**
            4. **Wrap your output in a single valid JSON object**, like this:

            ```json
            {{
            "analysis": "Brief explanation of what the question needs",
            "data_source": "sales_data" or a specific SQLite table or view (e.g., daily_250416_no_grand_total),
            "query": "SQL QUERY HERE",
            "explanation": "Why this query and data source are appropriate"
            }}
            ABSOLUTE RULES FOR SQL GENERATION:
            ✅ SYNTAX RULES (IMPORTANT)
            NEVER use column aliases (AS …) inside WHERE, HAVING, JOIN, or GROUP BY

            If you need to filter based on a derived column, use a subquery

            Prefer lowercase table and column names with underscores (e.g., sales_qty, purchase_qty)

            SQLite does NOT support advanced expressions like FILTER, LATERAL, CTE recursion, or WITH RECURSIVE

            Use explicit casting if dividing integers (e.g., CAST(sales_qty AS REAL))

            DO NOT use functions that are not supported in SQLite, such as:

            - NEVER use strftime() or any date functions in SQLite — they may not be supported in the environment.
            - Use plain string matching for dates (e.g., WHERE date LIKE '2025-04%' instead of strftime).

            NAMING NOTE:
            - Daily Excel files like salesninventory_YYMMDD.xlsx are loaded as SQLite tables named:
            → daily_YYMMDD
            → daily_YYMMDD_no_grand_total
            - DO NOT use the original filename like 'salesninventory_YYMMDD' in the query.
            - ALWAYS use 'daily_YYMMDD_no_grand_total' or equivalent for daily views.


            COALESCE is OK ✅

            FILTER, RANK, CUME_DIST, WITH ORDINALITY, etc. are ❌ NOT ALLOWED

            ✅ DATA RULES
            ALWAYS exclude "grand total" rows using:

            WHERE lower(brand) != 'grand total'

            Use the _no_grand_total view if available (e.g., daily_250416_no_grand_total)

            For percentage sold: (sales_qty / purchase_qty) * 100

            For estimated sell-out days:

            sql
            Copy
            Edit
            CASE WHEN sales_qty > 0 THEN (purchase_qty - sales_qty) / CAST(sales_qty AS REAL)
                ELSE NULL END
            CONTEXT YOU HAVE:
            DATA SOURCES (actual):
            {json.dumps(data_preview, indent=2, default=str)}

            SCHEMA OVERVIEW:
            Tables include columns like: brand, category, color, size, mrp, sales_qty, purchase_qty, date, week, month

            SQLite tables are created from Excel files and typically include views without “grand total” rows

            Postgres table sales_data is already structured and normalized

            USER'S QUESTION:
            "{question}"

            FINAL INSTRUCTIONS:
            Only return a JSON object with analysis, data_source, query, and explanation

            DO NOT explain or narrate outside the JSON

            DO NOT return markdown or headings

            Make sure the SQL is executable in the selected engine

            Prefer simplicity and correctness over cleverness

            ONLY return this:

            json
            Copy
            Edit
            {{ "analysis": "...", "data_source": "...", "query": "...", "explanation": "..." }}
            """
            
            print("Sending analysis prompt to Gemini...")
            # Generate the query plan
            response = model.generate_content(decision_prompt)
            query_plan_text = response.text
            
            # Extract and parse the JSON
            try:
                query_plan = self._extract_json(query_plan_text)
                print(f"Query plan: {json.dumps(query_plan, indent=2)}")
                
            except Exception as e:
                print(f"Error parsing query plan: {e}")
                query_plan = {
                    "analysis": "Could not parse the response properly",
                    "data_source": "sales_data" if self.data_sources["sales_data"]["status"] == "available" else "master_summary",
                    "query": "SELECT 1 as error",
                    "explanation": f"Error extracting query plan: {str(e)}"
                }
            # --- 👇 PATCH FOR INCORRECT DAILY TABLE NAME DETECTION ---
            invalid_table = query_plan.get("data_source", "")
            if invalid_table not in self.available_tables:
                match = re.search(r'(\d{6})', invalid_table)
                if match:
                    date_part = match.group(1)
                    corrected_table = f"daily_{date_part}_no_grand_total"
                    if corrected_table in self.available_tables:
                        print(f"Correcting invalid table reference from {invalid_table} to {corrected_table}")
                        # Update query and data source reference
                        query_plan["query"] = re.sub(re.escape(invalid_table), corrected_table, query_plan["query"])
                        query_plan["data_source"] = corrected_table
            # --- ✅ END PATCH ---

            
            
            # Execute the query on the appropriate data source
            if query_plan["data_source"] == "sales_data":
                if self.data_sources["sales_data"]["status"] == "available":
                    result = self.execute_neon_query(query_plan["query"])
                else:
                    result = {"error": "Neon DB is not available. Connection failed."}
            else:
                # For local Excel files, execute against our SQLite database
                # Make sure we have a connection
                if not self.conn:
                    if not self.available_tables:
                        result = {"error": "No local data sources are available"}
                    else:
                        result = {"error": "SQLite connection is not active"}
                else:
                    # Add _no_grand_total suffix if it's not already there and if it exists
                    data_source = query_plan["data_source"]
                    if data_source in ["master_summary", "daily_files"]:
                        # Use the original query if it's explicitly using the _no_grand_total view
                        if "_no_grand_total" not in query_plan["query"]:
                            # Check if we need to modify the query to exclude grand total rows
                            if "lower(brand) != 'grand total'" not in query_plan["query"].lower():
                                # Add a WHERE clause if there isn't one already
                                if "WHERE" not in query_plan["query"].upper():
                                    # Find the appropriate place to insert WHERE clause
                                    from_match = re.search(r'\sFROM\s+(\w+)', query_plan["query"], re.IGNORECASE)
                                    if from_match:
                                        table_name = from_match.group(1)
                                        if f"{table_name}_no_grand_total" in self.available_tables:
                                            # Replace the table with the _no_grand_total view
                                            query_plan["query"] = query_plan["query"].replace(
                                                f"FROM {table_name}", 
                                                f"FROM {table_name}_no_grand_total"
                                            )
                                            print(f"Modified query to use {table_name}_no_grand_total view")
                                        else:
                                            # Add a WHERE clause
                                            query_plan["query"] = query_plan["query"] + " WHERE lower(brand) != 'grand total'"
                                            print("Added WHERE clause to exclude grand total")
                                else:
                                    # Add to existing WHERE clause
                                    query_plan["query"] = query_plan["query"].replace(
                                        "WHERE", 
                                        "WHERE lower(brand) != 'grand total' AND "
                                    )
                                    print("Extended WHERE clause to exclude grand total")
                    
                    result = self.execute_sqlite_query(query_plan["query"])
            
            # Check for errors in the result
            if isinstance(result, dict) and "error" in result:
                error_details = result["error"]
                error_feedback_prompt = f"""
                There was an error when trying to execute the query to answer the user's question.
                
                User question: "{question}"
                
                Query plan: {json.dumps(query_plan, indent=2)}
                
                Error message: {error_details}
                
                Available data sources: {json.dumps(data_preview, indent=2, default=str)}
                
                Available SQLite tables: {', '.join(self.available_tables)}
                
                Please provide a helpful response to the user that:
                1. Acknowledges the error
                2. Explains what information you were trying to get
                3. Suggests what might be needed to properly answer their question
                4. Offers an alternative approach if possible
                
                Format your response in Markdown and make it conversational, concise, and helpful.
                
                Response:
                """
                
                response = model.generate_content(error_feedback_prompt)
                return response.text
            
            # Use Gemini to format the result into a natural language response
            format_prompt = f"""
            You are an expert business assistant AI trained in data storytelling.

            You are given:
            1. A user’s natural language **business question**
            2. A query plan showing which data source was used
            3. Raw query results (as rows of structured data)

            Your job is to write a **clear, visually engaging, and insightful** response that:
            - Answers the user’s question with real data
            - Highlights interesting patterns or problems
            - Gives a business-friendly interpretation
            - Suggests useful follow-ups where appropriate

            ---

            ## ✅ FORMAT RULES (MANDATORY)

            ### 🧠 INSIGHTFULNESS
            - Summarize the **key takeaway or answer** in 1-2 lines up top
            - Identify **trends, outliers, or thresholds crossed** (e.g., 75% sold items)
            - Include smart commentary like:
            - "This category is underperforming"
            - "Sales have accelerated in the past week"
            - "You might consider restocking these items soon"

            ### 🎨 VISUAL STRUCTURE (MARKDOWN)
            - Use headings like `## Summary`, `## Highlights`, `## Table of Results`, `## Suggestions`
            - Use bullet points for lists
            - Use tables for product listings, metrics, and sales comparisons
            - Use bold for key numbers, brands, or warnings
            - Use Horizontal Rules
            - Use Blockquotes
            - Use Bullet Graph / Rating Stars
            - Use emojis **sparingly** for visual cue (e.g., 🔥 for high sales, ⚠️ for low inventory and others depending on the word)
                - Use different innovative ad creative structures with appropriate colors to make visually appeling answers.

            ### 💡 VALUE-DRIVEN COMMUNICATION
            - Speak in business terms, not technical terms
            - Focus on outcomes, decisions, and actions, not database concepts
            - NEVER mention SQL, code, queries, rows, or data sources

            ---

            ## 📊 IF THE RESULT IS A TABLE:
            - Present it using Markdown with **clear, bold headers**
            - Include columns like: Brand, Category, MRP, SalesQty, PurchaseQty, % Sold, Days Left
            - Highlight important rows:
            - Use bold or emojis for items >75% sold or with low inventory
            - Truncate long tables to top 5–10 items with a note: "_showing top results_"

            ---

            ## 🤔 IF DATA SEEMS ODD OR INCOMPLETE:
            - Gently mention uncertainty or limitations (e.g., “This is based on limited data from the last snapshot.”)
            - Suggest how to get better answers: e.g., “Try asking about the full month trend.”

            ---

            ## 🔁 IF THE RESULT IS JUST SAMPLE DATA (FALLBACK):
            - Tell the user: “I had trouble answering that directly, but here’s a sample of what I can access right now.”
            - Suggest rephrasing or another angle

            If the question is about promotions, and no such column exists:
            - Explain this politely
            - Try using sales-to-purchase ratio or compare current vs. past sales
            - Suggest that adding a 'promotion' flag in the data might improve future answers

            ---

            ## USER QUESTION:
            "{question}"

            ## QUERY PLAN:
            {json.dumps(query_plan, indent=2)}

            ## RAW DATA RESULT:
            {json.dumps(result, indent=2, default=str)}

            ---

            ## YOUR TASK:
            Write a fully polished business answer using the structure above. Be sharp, natural, friendly, and insightful.
            Use Markdown headings and formatting.

            **Final Output: Only the user-facing message. No debug info.**
            """

            
            print("Sending formatting prompt to Gemini...")
            response = model.generate_content(format_prompt)
            print("Formatted response received.")
            return response.text
        
        except Exception as e:
            print(f"Error processing question: {str(e)}")
            error_traceback = sys.exc_info()[2]
            import traceback
            error_details = "".join(traceback.format_tb(error_traceback))
            return f"""
            ## Error Processing Request
            
            I encountered an error while processing your question:
            
            **Error**: {str(e)}
            
            This might be due to missing data or a technical issue. Could you try:
            
            - Asking a more specific question
            - Checking that your data files are correctly formatted
            - Ensuring your database connections are properly configured
            
            If the issue persists, please review the application logs for more detailed information.
            """
    
    def _extract_json(self, text):
        """Extract JSON from text response"""
        # Find JSON pattern in the text
        match = re.search(r'({[\s\S]*})', text)
        if match:
            try:
                # Try to parse the entire matched text as JSON
                json_str = match.group(1)
                return json.loads(json_str)
            except json.JSONDecodeError:
                # If direct parsing fails, try to clean the string and try again
                json_str = match.group(1)
                # Remove markdown code block markers
                json_str = re.sub(r'```(?:json)?\s*|\s*```', '', json_str)
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    # More aggressive cleaning
                    json_str = re.sub(r'[^\x00-\x7F]+', '', json_str)  # Remove non-ASCII
                    return json.loads(json_str)
        
        # If we couldn't find or parse JSON, raise an exception
        raise ValueError("Could not extract valid JSON from response")

print("Creating global chatbot instance...")
chatbot_instance = SalesDataChatbot()

def chat(question: str) -> str:
    """
    Handles a user question by processing it through the global chatbot instance.
    Args:
        question: The user's question string.
    Returns:
        The chatbot's response string (likely Markdown formatted).
    """
    if not isinstance(question, str) or not question.strip():
        return "## Error\n\nPlease provide a valid question."

    # Call the process method on the global instance
    response = chatbot_instance.process_user_question(question)
    return response

# --- Cleanup Function (Optional, for specific Flask shutdown hooks if needed) ---
def cleanup_chatbot():
    """Function to explicitly call cleanup on the global instance."""
    print("Attempting chatbot cleanup...")
    chatbot_instance.cleanup()