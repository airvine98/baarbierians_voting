from datetime import datetime
import os

import numpy as np
import pandas as pd
import psycopg2
import streamlit as st
import yaml

st.title("Baarbierians Voting Form")
# st.write("Fill out the date of the voting, the name of the voting organiser and the results of each category including whether the winner was in the pub or not. After submitting the form, a message will appear at the bottom of the page which can be posted in the Whatsapp group.")

# Get database connection

# Function to get database connection
def get_connection():
    config = yaml.safe_load(open("config.yml"))

    return psycopg2.connect(
        dbname=config['dbname'],
        user=config['user'], 
        password=config['password'], 
        host=config['host'],
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

    results = pd.DataFrame(index=categories.keys(), columns=["Winner", "In Pub", "Points"])

    for category, positive in categories.items():
        winner = st.selectbox(category, players, index=None)
        if winner == "Other":
            winner = st.text_input(f"New player:", key=f"new_player_{category}")
            players.insert(0, winner)
            players = sorted(players[:-1]) + players[-1:]

        in_pub = (st.radio(f"In the Pub?", ("Yes", "No"),
                  key=f"{category}, in pub") == "Yes")

        if positive:
            points = 1
        else:
            points = -1

        if not in_pub:
            points -= 1

        results.loc[category] = [winner, in_pub, points]

    submitted = st.button("Submit")

    if submitted:
        if None in results["Winner"].values or filled_by is None:
            missing_vals = []
            if filled_by is None:
                missing_vals.append("Voting Host")
            missing_vals = missing_vals + results[results["Winner"].isnull()].index.tolist()
            error_string = "Please select names for these fields: " + ", ".join(missing_vals)
            st.error(error_string)
        else:
            output = f"**WhatsApp message:**\n\nVoting results {date.strftime('%d.%m.%Y')}:\n"
            query_string = "INSERT INTO votes (date, filled_by, category, winner, in_pub, points) VALUES "
            for ind in results.index:
                output += f'  \n{ind}: {results.at[ind, "Winner"]} ({results.at[ind, "Points"]})'
                query_string += f"('{date.strftime('%Y-%m-%d')}', '{filled_by}', '{ind}', '{results.at[ind, 'Winner']}', {str(results.at[ind, 'In Pub']).upper()}, {results.at[ind, 'Points']}), "
            query_string = query_string[:-2]
            query_string += " ON CONFLICT (date, category) DO UPDATE SET filled_by = EXCLUDED.filled_by, winner = EXCLUDED.winner, in_pub = EXCLUDED.in_pub, points = EXCLUDED.points;"
            query_string = query_string.replace("Captain's Performance", "Captains Performance")
            cursor.execute(query_string)
            conn.commit()
            st.write(output)
