from sqlalchemy import create_engine, text
import yaml

# Function to get database connection
def get_connection():
    config = yaml.safe_load(open("config.yml"))

    return create_engine(f"mysql+mysqlconnector://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['dbname']}", echo=True).connect()

# Function to check database connection
def check_connection():
    try:
        conn = get_connection()
        
        # Execute query to check connection
        result = conn.execute(text("SELECT NOW();"))
        
        # Fetch the result
        value = result.fetchone()[0]
        print("Connection successful. Current date and time:", value)
        
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        # Close connection
        conn.close()

check_connection()