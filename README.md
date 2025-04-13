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

Explore InventorySync’s intuitive navigation pages through these screenshots, showcasing each section’s functionality.

![image](https://github.com/user-attachments/assets/abababdb-ead1-483b-bf27-bb2830897cb6)

![image](https://github.com/user-attachments/assets/4a7c84a2-df25-435a-bc70-0ce7b73f95e1)

![image](https://github.com/user-attachments/assets/ee499184-7e3f-4c30-99b3-d6c50f636767)

![image](https://github.com/user-attachments/assets/b33c6dac-1a58-4a99-a62f-b7f101b1db61)

![image](https://github.com/user-attachments/assets/ebd4877b-5d78-4c6a-a475-27f98f0ebc13)

![image](https://github.com/user-attachments/assets/91eec5d2-80a1-4122-a130-afe41c28e065)

![image](https://github.com/user-attachments/assets/7cf90f56-34d0-4ec1-9ec4-3179cf00847b)

![image](https://github.com/user-attachments/assets/42461396-06f9-497a-8ee2-634ecfa204ad)

---

## 📜 License

InventorySync is licensed under the [MIT License](LICENSE).

---
## 🌍 Join the Future of Business Management

InventorySync isn’t just a tool—it’s your co-pilot for navigating the cosmos of sales and inventory data. Star the repo ⭐ :)

---

*Built with 💻 and ☕ by [Myron Correia] and the InventorySync community.*

---
