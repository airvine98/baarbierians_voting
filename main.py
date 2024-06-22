from datetime import datetime
import os

import numpy as np
import pandas as pd
import psycopg2
import streamlit as st

st.title("Baarbierians Voting Form")
# st.write("Fill out the date of the voting, the name of the voting organiser and the results of each category including whether the winner was in the pub or not. After submitting the form, a message will appear at the bottom of the page which can be posted in the Whatsapp group.")

# Get database connection


def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("dbname"),
        user=os.getenv("user"),
        password=os.getenv("password"),
        host=os.getenv("host"),
    )


if __name__ == "__main__":
    # Define categories
    categories = {"Goal of the night": True,
                  "Save of the night": True,
                  "Skill Moment": True,
                  "Worst Tackle": False,
                  "Duffer": False,
                  "Drama Queen": False,
                  "Greedy Bastard": False,
                  "Golden Goal": True,
                  "Captain's Performance": True}

    # Define organisers
    # TODO: Should be read in from the database
    organisers = ["Andrew", "Alistair", "Andy", "Scott",
                  "Mark H", "Mark B", "Gary", "Panu", "Carlo", "Simon"]
    organisers.sort()
    organisers.append("Other")

    # Define players
    # TODO: Should be read in from the database
    players = ["Andrew", "Alistair", "Andy", "Scott",
               "Mark H", "Mark B", "Gary", "Panu", "Carlo", "Simon"]
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
        if winner == "Add New Player":
            winner = st.text_input(f"New player:")
            players.add(winner)

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
            output = f"Voting results {date.strftime('%d.%m.%Y')}:\n"
            for row in results:
                output += f'\n{row.index}: {row.at["Winner"]} ({row.at["Points"]})'
            st.write(output)
