import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables from a .env file
load_dotenv()

# Function to get database connection
def get_connection():
    return psycopg2.connect(
        dbname=os.getenv('dbname'),
        user=os.getenv('user'), 
        password=os.getenv('password'), 
        host=os.getenv('host'),
    )

# Function to check database connection
def check_connection():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Execute query to check connection
        cursor.execute("SELECT NOW();")
        
        # Fetch the result
        result = cursor.fetchone()
        print("Connection successful. Current date and time:", result)
        
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        # Close cursor and connection
        cursor.close()
        conn.close()

check_connection()