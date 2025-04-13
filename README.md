# 🚀 InventorySync - Your AI-Powered Business Navigator 🌌

Welcome to **InventorySync**, the ultimate AI-driven business assistant that revolutionizes how you manage sales and inventory data! Built with cutting-edge technology, InventorySync offers a seamless web interface, intelligent data processing, and a conversational chatbot to empower your business decisions. Ready to sync your data and soar to new heights? Let’s dive in! ✨

[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-2.0%2B-green)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-yellow)](https://opensource.org/licenses/MIT)

---

## 🌟 What is InventorySync?

InventorySync is a futuristic platform designed to streamline your sales and inventory management. Powered by **Flask** for a robust backend, **PostgreSQL** for secure data storage, and the **Gemini API** for an intuitive chatbot, it’s your one-stop solution for data-driven insights. Whether you’re uploading datasets, visualizing trends, or querying sales stats, InventorySync delivers with style and precision.

### Key Features
- 📤 **Data Upload & Processing**: Effortlessly upload Excel files and preprocess data for analysis.
- 📊 **Data Preview**: Get a quick snapshot of your datasets with clean, tabulated views.
- 📁 **Local File Management**: Organize and manage files directly from the interface.
- 📈 **Visualizations**: Generate stunning charts and graphs to uncover trends.
- 🤖 **AI Chatbot**: Ask questions like “What’s my top product this quarter?” and get instant, conversational answers.

---

## 🛠️ Installation

Get InventorySync up and running in minutes with these simple steps:

1. **Clone the Repository**  
   ```bash
   git clone https://github.com/yourusername/inventorysync.git
   cd inventorysync
   ```

2. **Set Up a Virtual Environment**  
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**  
   Install the required packages to power InventorySync:  
   ```bash
   pip install flask pandas numpy psycopg2-binary sqlalchemy plotly matplotlib seaborn google-generativeai python-dotenv
   ```

4. **Prerequisites**  
   - Python 3.8 or higher
   - A PostgreSQL database (e.g., Neon DB)
   - A Gemini API key for chatbot functionality

---

## 🔧 Configuration

To unlock InventorySync’s full potential, configure your environment variables:

1. Create a `.env` file in the project root:  
   ```bash
   touch .env
   ```

2. Add the following variables:  
   ```env
   NEON_DB_URL=your_postgresql_connection_string
   GEMINI_API_KEY=your_gemini_api_key
   ```

3. Ensure `.env` is added to `.gitignore` to keep sensitive data secure.

---

## 🚀 Getting Started

Launch InventorySync and explore its galactic features:

1. **Run the Application**  
   Start the Flask server:  
   ```bash
   python data.py
   ```

2. **Access the Web Interface**  
   Open your browser and navigate to `http://localhost:5000` to enter the InventorySync dashboard.

3. **Explore the Features**  
   - **Upload Data**: Drag and drop Excel files to ingest sales and inventory data.
   - **Preview Data**: View clean, tabulated summaries of your datasets.
   - **Manage Files**: Organize local files with ease.
   - **Visualize Insights**: Generate interactive charts to spot trends.
   - **Chat with the AI**: Ask questions like:  
     - “What’s the total sales for this month?”  
     - “Which product has the highest revenue?”  
     - “Show me sales trends for 2025.”

---

## 🌐 Example Usage

Here’s a taste of what InventorySync can do:

1. **Upload a Dataset**  
   Upload an Excel file with sales data (e.g., `sales_2025.xlsx`). InventorySync processes it and stores it in PostgreSQL.

2. **Preview Your Data**  
   Check the data preview tab to see a tabulated view of your sales records.

3. **Visualize Trends**  
   Navigate to the insights section to generate a bar chart of monthly sales or a pie chart of product categories.

4. **Chat with the AI**  
   In the chatbot tab, type:  
   ```
   What’s the top-selling product this quarter?
   ```
   Get a response like:  
   > The top-selling product this quarter is **Widget X** with 1,200 units sold, generating $24,000 in revenue.

---

## 📜 License

InventorySync is licensed under the [MIT License](LICENSE).

---

## 🌍 Join the Future of Business Management

InventorySync isn’t just a tool—it’s your co-pilot for navigating the cosmos of sales and inventory data. Star the repo, try it out, and let’s build the future together! ⭐

---

*Built with 💻 and ☕ by [Myron Correia] and the InventorySync community.*
