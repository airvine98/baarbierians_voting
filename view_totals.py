import pandas as pd
from sqlalchemy import create_engine
import yaml


# Function to get database connection
def get_connection():
    config = yaml.safe_load(open("config.yml"))

    return create_engine(f"postgresql+psycopg2://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['dbname']}")



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
    
    engine = get_connection()

    # votes_query = f"TRUNCATE TABLE votes;"
    # cursor.execute(votes_query)

    for category, positive in categories.items():
        totals_query = f"SELECT * FROM {category.lower().replace(' ', '_')} ORDER BY points {'DESC' if positive else 'ASC'}, votes_won DESC;"
        totals_query = totals_query.replace("n's", "ns")
        df = pd.read_sql(totals_query, engine, index_col="name")
        print(f"\n\n\n{category}\n", df.head(10))