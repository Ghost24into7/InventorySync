# 🚀 InventorySync - Your AI-Powered Business Navigator 🌌

Welcome to **InventorySync**, the ultimate AI-driven business assistant that transforms how you manage sales and inventory data! With a sleek web interface, intelligent data processing, and a conversational chatbot, InventorySync empowers you to make data-driven decisions with ease. Ready to sync your data and explore the future of business management? Let’s blast off! ✨

[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-2.0%2B-green)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-yellow)](https://opensource.org/licenses/MIT)
[![GitHub Stars](https://img.shields.io/github/stars/Ghost24into7/inventorysync?style=social)](https://github.com/Ghost24into7/InventorySync.git)

---

## 🌟 What is InventorySync?

InventorySync is a cutting-edge platform designed to streamline sales and inventory management. Powered by **Flask** for a robust backend, **PostgreSQL** for secure data storage, and the **Gemini API** for an intuitive AI chatbot, it’s your all-in-one solution for actionable insights. From uploading datasets to visualizing trends and querying sales stats, InventorySync delivers with precision and style.

### Key Features
- 📤 **Data Upload & Processing**: Seamlessly upload Excel files and preprocess data for analysis.
- 📊 **Data Preview**: View clean, tabulated snapshots of your datasets.
- 📁 **Local File Management**: Organize and manage files directly from the interface.
- 📈 **Visualizations**: Create stunning charts and graphs to uncover trends.
- 🤖 **AI Chatbot**: Ask questions like “What’s my top product this quarter?” and get instant answers.

---

## 🛠️ Installation

Set up InventorySync in minutes with these steps:

1. **Clone the Repository**  
   ```bash
   git clone https://github.com/Ghost24into7/InventorySync.git
   cd inventorysync
   ```

2. **Set Up a Virtual Environment**  
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**  
   Install the required packages:  
   ```bash
   pip install flask pandas numpy psycopg2-binary sqlalchemy plotly matplotlib seaborn google-generativeai python-dotenv
   ```

4. **Prerequisites**  
   - Python 3.8 or higher
   - A PostgreSQL database (e.g., Neon DB)
   - A Gemini API key for chatbot functionality

---

## 🔧 Configuration

Unlock InventorySync’s full potential by configuring your environment:

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

Launch InventorySync and dive into its galactic features:

1. **Run the Application**  
   Start the Flask server:  
   ```bash
   python data.py
   ```

2. **Access the Web Interface**  
   Open your browser and navigate to `http://localhost:5000` to explore the InventorySync dashboard.

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

Here’s how InventorySync works in action:

1. **Upload a Dataset**  
   Upload an Excel file (e.g., `sales_2025.xlsx`). InventorySync processes it and stores it in PostgreSQL.

2. **Preview Your Data**  
   Check the data preview tab for a tabulated view of your sales records.

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

Below is the **Screenshots** section of the **README.md** for your **InventorySync** project, focusing exclusively on the navigation pages as requested. Since the project’s frontend (`other.html`) is a single-page application with distinct sections (Dashboard, Data Upload, Data Preview, Visualizations, and Chatbot) accessible via navigation, this section includes screenshots for each of these pages. Each page has two side-by-side images to showcase different aspects of the interface, with brief descriptions for context. The images are properly aligned using Markdown tables for a modern, clean layout. Placeholder image paths are used, as actual screenshots need to be captured from the running application.

---

## 🖼️ Screenshots

Explore InventorySync’s intuitive navigation pages through these screenshots, showcasing each section’s functionality. Each page includes two side-by-side images for a comprehensive view, along with a description of its purpose.

### 📋 Dashboard
The Dashboard serves as the central hub, providing quick access to all features—upload, preview, file management, visualizations, and the chatbot.

| **Dashboard Overview** | **Feature Navigation** |
|------------------------|------------------------|
| ![Dashboard Overview](![image](https://github.com/user-attachments/assets/87f1b7bb-f8ea-45f6-87d9-5a5a99030b43)) | ![Feature Navigation](![image](https://github.com/user-attachments/assets/c531cfb7-343f-459f-a564-adcdbb2ec605)) |

### 📊 Data Preview
The Data Preview page displays your datasets in a clean, tabulated format, with options to filter and sort.

| **Table View** | **Filtered Data** |
|----------------|-------------------|
| ![Table View](![image](![image](https://github.com/user-attachments/assets/2538ec8b-6d7a-429c-b25e-9f4cb0aa2de3))) | ![Filtered Data]() |

### 📈 Visualizations
The Visualizations page generates interactive charts, such as bar graphs and pie charts, to uncover trends in your data.

| **Bar Chart View** | **Pie Chart View** |
|--------------------|--------------------|
| ![Bar Chart View](images/screenshots/visualization_bar.png) | ![Pie Chart View](images/screenshots/visualization_pie.png) |

### 🤖 Chatbot
The Chatbot page offers a conversational interface to query sales and inventory data, powered by the Gemini API.

| **Chat Interface** | **Query Response** |
|--------------------|--------------------|
| ![Chat Interface](images/screenshots/chatbot_interface.png) | ![Query Response](images/screenshots/chatbot_response.png) |

---

## 📜 License

InventorySync is licensed under the [MIT License](LICENSE).

---
## 🌍 Join the Future of Business Management

InventorySync isn’t just a tool—it’s your co-pilot for navigating the cosmos of sales and inventory data. Star the repo, try it out, and let’s shape the future together! ⭐

---

*Built with 💻 and ☕ by [Myron Correia] and the InventorySync community.*

---
