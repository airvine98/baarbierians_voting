from sqlalchemy import URL, create_engine, text
import yaml

# Function to get database connection
def get_connection():
    config = yaml.safe_load(open("config.yml", "r"))

    DB_NAME = config['dbname']
    DB_USER = config['user']
    DB_PASSWORD = config['password']
    DB_HOST = config['host']
    DB_PORT = config['port']

    url = URL.create(
        drivername="mysql+mysqlconnector",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=int(DB_PORT),
        database=DB_NAME,
    )

    return create_engine(url, echo=True).connect()

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