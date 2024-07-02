import psycopg2
import yaml

# Function to get database connection
def get_connection():
    config = yaml.safe_load(open("config.yml"))

    return psycopg2.connect(
        dbname=config['dbname'],
        user=config['user'], 
        password=config['password'], 
        host=config['host'],
    )

# Function to check database connection
def check_connection():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Execute query to check connection
        cursor.execute("SELECT NOW();")
        
        # Fetch the result
        result = cursor.fetchone()[0]
        print("Connection successful. Current date and time:", result)
        
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        # Close cursor and connection
        cursor.close()
        conn.close()

check_connection()