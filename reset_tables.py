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
        port=config['port']
    )



if __name__ == "__main__":
    # Define categories
    categories = {"Goal of the Night": True,
                  "Save of the Night": True,
                  "Skill Moment": True,
                  "Worst Tackle": False,
                  "Duffer": False,
                  "Drama Queen": False,
                  "Greedy Bastard": False,
                  "Golden Goal": True,
                  "Captain's Performance": True}
    
    conn = get_connection()
    cursor = conn.cursor()

    # votes_query = f"TRUNCATE TABLE votes;"
    # cursor.execute(votes_query)

    for category in categories.keys():
        totals_query = f"TRUNCATE TABLE {category.lower().replace(' ', '_')};"
        # totals_query = f"CREATE TABLE {category.lower().replace(' ', '_')} (name VARCHAR(100) NOT NULL, votes_won INTEGER NOT NULL, points INTEGER NOT NULL, PRIMARY KEY (name));"
        totals_query = totals_query.replace("n's", "ns")
        cursor.execute(totals_query)
    
    conn.commit()