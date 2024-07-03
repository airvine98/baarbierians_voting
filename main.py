from datetime import datetime
import os

from dotenv import load_dotenv
import pandas as pd
import psycopg2
import streamlit as st
# import yaml

TOTALS_START_DATE = "2023-11-11"

load = load_dotenv()

st.title("Baarbierians Voting Form")
# st.write("Fill out the date of the voting, the name of the voting organiser and the results of each category including whether the winner was in the pub or not. After submitting the form, a message will appear at the bottom of the page which can be posted in the Whatsapp group.")
# Read environment variables
db_name = os.getenv('dbname')
db_user = os.getenv('user')
db_password = os.getenv('password')
db_host = os.getenv('host')


# Function to get database connection
def get_connection():
    # config = yaml.safe_load(open("config.yml"))

    # return psycopg2.connect(
    #     dbname = config["dbname"],
    #     user = config["user"],
    #     password = config["password"],
    #     host = config["host"]
    # )

    return psycopg2.connect(
        dbname = db_name,
        user = db_user,
        password = db_password,
        host = db_host
    )


@st.experimental_dialog("Check your submission and confirm")
def submission_popup():
    message = f"**Voting results {date.strftime('%d.%m.%Y')}:**  \n"
    for category in results["Category"].unique():
        message += f'  \n{category}: ' +  ", ".join([f'{winner}  ({points})' for winner, points in results[results["Category"]==category][["Winner", "Points"]].values])
    st.write(message)
    placeholder = st.empty()
    confirm = placeholder.button("Confirm")
    if confirm:
        clear_date_query = f"DELETE FROM votes WHERE date = '{date.strftime('%Y-%m-%d')}';"
        cursor.execute(clear_date_query)
        votes_query = "INSERT INTO votes (date, filled_by, category, winner_num, winner, in_pub, points) VALUES "
        for ind in results.index:
            votes_query += f"('{date.strftime('%Y-%m-%d')}', '{filled_by}', '{results.at[ind, 'Category']}', {results.at[ind, 'Winner Number']}, '{results.at[ind, 'Winner']}', {str(results.at[ind, 'In Pub']).upper()}, {results.at[ind, 'Points']}), "
        votes_query = votes_query[:-2]
        votes_query += " ON CONFLICT (date, category, winner_num) DO UPDATE SET filled_by = EXCLUDED.filled_by, winner = EXCLUDED.winner, in_pub = EXCLUDED.in_pub, points = EXCLUDED.points;"
        votes_query = votes_query.replace("n's", "ns")
        cursor.execute(votes_query)
        for category in categories.keys():
            totals_query = f"TRUNCATE TABLE {category.lower().replace(' ', '_')};"
            totals_query += f"INSERT INTO {category.lower().replace(' ', '_')} (name, votes_won, points) SELECT winner, COUNT(*), SUM(points) FROM votes WHERE category = '{category}' AND date >= '{TOTALS_START_DATE}' GROUP BY winner ON CONFLICT (name) DO UPDATE SET votes_won = EXCLUDED.votes_won, points = EXCLUDED.points;"
            totals_query = totals_query.replace("n's", "ns")
            cursor.execute(totals_query)
        conn.commit()
        output = "**Votes submitted**  \nPlease copy the votes above and send in the WhatsApp group."
        st.warning(output, icon=":material/check_circle:")
        placeholder.empty()



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

    # Fetch organisers
    cursor.execute("SELECT DISTINCT filled_by FROM votes WHERE date > CURRENT_DATE - INTERVAL '3 years';")
    organisers = [val[0] for val in cursor.fetchall()]
    organisers.sort()
    organisers.append("Other")
    

    # Fetch players
    cursor.execute("SELECT DISTINCT winner FROM votes WHERE date > CURRENT_DATE - INTERVAL '3 years';")
    players = [val[0] for val in cursor.fetchall()]
    players.sort()
    players.append("Other")

    # Date input outside the form
    date = st.date_input("Date", datetime.now(), format="DD.MM.YYYY")

    # Voting organiser selection outside the form
    filled_by = st.selectbox("Voting Host", organisers, index=None)

    # Conditional input for "Other" organiser
    if filled_by == "Other":
        filled_by = st.text_input("Enter organiser name")

    results = pd.DataFrame(columns=["Category", "Winner Number", "Winner", "In Pub", "Points"])

    for category, positive in categories.items():
        st.write(category)
        with st.container(border=True):
            col1, col2 = st.columns([1,6])
            with col1:
                num_winners = st.number_input("Number of winners", 1, 11, step=1, key=f"num_winners_{category}")
            with col2:
                winners = []
                in_pub = []
                for i in range(num_winners):
                    with st.container():
                        subcol1, subcol2 = st.columns([5,1])
                        with subcol1:
                            winners.append(st.selectbox(f"Winner {i+1}", players, index=None, key=f"winner_{category}_{i}"))
                            if winners[i] == "Other":
                                winners[i] = st.text_input(f"New player:", key=f"new_player_{category}_{i}")
                                players.insert(0, winners[i])
                                players = sorted(players[:-1]) + players[-1:]
                
                        with subcol2:
                            in_pub.append((st.radio(f"In the Pub?", ("Yes", "No"),
                                key=f"in_pub_{category}_{i}") == "Yes"))


            if positive:
                points = [1] * num_winners
            else:
                points = [-1] * num_winners

            for i in range(num_winners):
                if not in_pub[i]:
                    points[i] -= 1
            
            for i in range(num_winners):
                results.loc[len(results.index)] = [category, i+1, winners[i], in_pub[i], points[i]]
    
    results.replace("", None, inplace=True)

    submitted = st.button("Submit")

    if submitted:
        if None in results["Winner"].values or filled_by is None:
            missing_vals = []
            if filled_by is None:
                missing_vals.append("  \nVoting Host")
            missing_vals = missing_vals + [f'  \n{results.at[idx, "Category"]} (Winner {results.at[idx, "Winner Number"]})' for idx in results[results["Winner"].isnull()].index]
            error_string = "Please select names for these fields: " + ", ".join(missing_vals)
            st.error(error_string)
        else:
            submission_popup()
