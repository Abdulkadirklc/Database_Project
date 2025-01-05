# **Event Management System API**

  This project is a RESTful API for managing events. 
---

## **Setup and Installation**

Follow these steps to set up and run the project on your local machine:

### **1. Install Requirements**
Install the required Python packages using `pip`:
```bash
pip install -r requirements.txt
```

### **2. Create Database and Tables**
To set up your database, follow these steps:

1. Open the `create_database/create_tables.py` file and locate the database configuration section:
   ```python
   # Database configuration
   DB_HOST = 'your_db_host'
   DB_USER = 'your_db_username'
   DB_PASSWORD = 'your_db_password'  
   DB_NAME = 'event_management'
   ```

2. Open a terminal and navigate to the project directory.

3. Execute the script using the following command:
   ```bash
   python create_tables.py
   ```

### **3. Start the Application**
To start the application, follow these steps:

1. Open the `routes/__init__.py` file and locate the database configuration section:
   ```python
   # Database configuration
   DB_HOST = 'your_db_host'
   DB_USER = 'your_db_username'
   DB_PASSWORD = 'your_db_password'  
   DB_NAME = 'event_management'
   ```
2. Open a terminal and navigate to the project directory.

3. Execute the script using the following command:
   ```bash
   python app.py
   ```
### **4. Insert Dummy Data via API**
To insert dummy data via API:

1. Open a terminal and navigate to the create_database folder.

2. Execute the script using the following command:
   ```bash
   python insert_dummy_data.py
   ```
   
   Note: While inserting into `Membership`, you might see some errors on the terminal, this is due to existing `Group` admins, so there is nothing wrong with those errors.
   
### 5. Access API Documentation
Once the application is running, you can access the Swagger documentation to explore the API:

1. If the browser does not open automatically, manually navigate to the following URL:
```bash
http://127.0.0.1:5000/docs
```

2. The Swagger UI will display a list of available API endpoints, including their request methods, parameters, and example responses.

3. Use the Swagger interface to test the API directly by sending requests and viewing responses.

If the Swagger UI does not load, ensure that:
- The `app.py` file is running without errors.
