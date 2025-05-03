from datetime import datetime
import os

from dotenv import load_dotenv
import pandas as pd
import psycopg2
import streamlit as st
# import yaml

load = load_dotenv()

def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        # If you use .streamlit/secrets.toml, replace os.getenv with st.secrets["STREAMLIT_PASSWORD"]
        if st.session_state["password"] == os.getenv("STREAMLIT_PASSWORD"):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("Password incorrect")
    return False

st.markdown(
    """
        <style>
               .block-container {
                    padding-top: 1rem;
                    padding-bottom: 0rem;
                    padding-left: 0rem;
                    padding-right: 0rem;
                }
        </style>
        """,
    unsafe_allow_html=True,
)

# Read environment variables
DB_NAME = os.getenv('dbname')
DB_USER = os.getenv('user')
DB_PASSWORD = os.getenv('password')
DB_HOST = os.getenv('host')


# Define categories and if positive
CATEGORIES = {"Goal of the Night": True,
            "Save of the Night": True,
            "Skill Moment": True,
            "Worst Tackle": False,
            "Duffer": False,
            "Drama Queen": False,
            "Greedy Bastard": False,
            "Golden Goal": True,
            "Captain's Performance": True}


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
        dbname = DB_NAME,
        user = DB_USER,
        password = DB_PASSWORD,
        host = DB_HOST
    )


@st.dialog("Check your submission and confirm")
def submission_popup():
    if len(missing_opt_vals) > 0:
        st.warning("**Warning:** The following optional fields are empty." + ", ".join(missing_opt_vals), icon=":material/warning:")
    message = f"**Voting results {date.strftime('%d.%m.%Y')}:**  \n"
    for category in results["Category"].unique():
        message += f'  \n{category}: ' +  ", ".join([f'{winner}  ({points})' if winner is not None else "None" for winner, points in results[results["Category"]==category][["Winner", "Points"]].values])
    st.write(message)
    placeholder = st.empty()
    confirm = placeholder.button("Confirm")
    if confirm:
        placeholder.empty()
        clear_date_query = f"DELETE FROM votes WHERE date = '{date.strftime('%Y-%m-%d')}';"
        cursor.execute(clear_date_query)
        votes_query = "INSERT INTO votes (date, filled_by, category, winner_num, winner, in_pub, points) VALUES "
        for ind in results.index:
            if results.at[ind, 'Winner'] is not None:
                votes_query += f"('{date.strftime('%Y-%m-%d')}', '{filled_by}', '{results.at[ind, 'Category']}', {results.at[ind, 'Winner Number']}, '{results.at[ind, 'Winner']}', {str(results.at[ind, 'In Pub']).upper()}, {results.at[ind, 'Points']}), "
        votes_query = votes_query[:-2]
        votes_query += " ON CONFLICT (date, category, winner_num) DO UPDATE SET filled_by = EXCLUDED.filled_by, winner = EXCLUDED.winner, in_pub = EXCLUDED.in_pub, points = EXCLUDED.points;"
        votes_query = votes_query.replace("Captain's", "Captains")
        cursor.execute(votes_query)
        conn.commit()
        output = "**Votes submitted**  \nPlease copy the votes above and send in the WhatsApp group."
        st.success(output, icon=":material/check_circle:")


def get_info_for_date():
    try:
        cursor.execute(f"SELECT * FROM votes WHERE date = '{st.session_state['date'].strftime('%Y-%m-%d')}';")
    except:
        cursor.execute(f"SELECT * FROM votes WHERE date = '{datetime.now().strftime('%Y-%m-%d')}';")
    votes = cursor.fetchall()

    try:
        votes = pd.DataFrame(votes, columns=["Host", "Date", "Category", "Winner", "In Pub", "Points", "Winner Number"])
        st.session_state["filled_by"] = votes["Host"].iat[0]
    except:
        votes = pd.DataFrame(columns=["Host", "Date", "Category", "Winner", "In Pub", "Points", "Winner Number"])
        st.session_state["filled_by"] = None

    for category in CATEGORIES.keys():
        if category.replace("Captain's", "Captains") in votes["Category"].unique(): 
            st.session_state["num_winners_" + category] = int(votes.loc[votes["Category"]==category.replace("Captain's", "Captains")]["Winner Number"].max())

            for i in range(st.session_state["num_winners_" + category]):
                st.session_state["winner_" + category + "_" + str(i+1)] = votes.loc[votes["Category"]==category.replace("Captain's", "Captains")].iloc[i]["Winner"]
                st.session_state["in_pub_" + category + "_" + str(i+1)] = "Yes" if votes.loc[votes["Category"]==category.replace("Captain's", "Captains")].iloc[i]["In Pub"] else "No"
        else:
            st.session_state["num_winners_" + category] = 1

            for i in range(st.session_state["num_winners_" + category]):
                st.session_state["winner_" + category + "_" + str(i+1)] = None
                st.session_state["in_pub_" + category + "_" + str(i+1)] = "Yes"


@st.fragment
def voting_host():
    filled_by = st.selectbox("Voting Host", hosts, key="filled_by", index=None)

    # Conditional input for "Other" host
    if filled_by == "Other":
        filled_by = st.text_input("Enter host name")

    return filled_by


if __name__ == "__main__":

    with st.spinner("Loading ..."):

        st.title("Baarbierians Voting Form")

        if not check_password():
            st.stop()

        conn = get_connection()
        cursor = conn.cursor()

        # Fetch hosts
        cursor.execute("SELECT DISTINCT filled_by FROM votes WHERE date > CURRENT_DATE - INTERVAL '3 years';")
        hosts = [val[0] for val in cursor.fetchall()]
        hosts.sort()
        hosts.append("Other")
        

        # Fetch players
        cursor.execute("SELECT DISTINCT winner FROM votes WHERE date > CURRENT_DATE - INTERVAL '3 years';")
        players = [val[0] for val in cursor.fetchall()]
        players.sort()
        players.append("Other")

        if "date" not in st.session_state.keys():
            get_info_for_date()

        # Date selector
        date = st.date_input("Date", "today", key="date", format="DD.MM.YYYY", on_change=get_info_for_date)

        # Voting host selection outside the form
        filled_by = voting_host()

        results = pd.DataFrame(columns=["Category", "Winner Number", "Winner", "In Pub", "Points"])

        for category, positive in CATEGORIES.items():
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
                                winners.append(st.selectbox(f"Winner {i+1}", players, index=None, key=f"winner_{category}_{i+1}"))
                                if winners[i] == "Other":
                                    winners[i] = st.text_input(f"New player:", key=f"new_player_{category}_{i+1}")
                                    players.insert(0, winners[i])
                                    players = sorted(players[:-1]) + players[-1:]
                    
                            with subcol2:
                                in_pub.append((st.radio(f"In the Pub?", ("Yes", "No"),
                                    key=f"in_pub_{category}_{i+1}") == "Yes"))


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

        submitted = st.button("Submit", key="submit", use_container_width=True)
        
    if submitted:
        missing_req_vals = []
        missing_opt_vals = []
        if filled_by is None:
            missing_req_vals.append("  \nVoting Host")
        for category in results.loc[results["Winner"].isnull()]["Category"].unique():
            if len(results.loc[(results["Winner"].isnull()) & (results["Category"]==category)].index) > 1:
                missing_req_vals.append(f'  \n{category} ({", ".join(["Winner " + str(i) for i in results.loc[(results["Winner"].isnull()) & (results["Category"]==category)]["Winner Number"]])})')
            else:
                missing_opt_vals.append(f'  \n{category} ({", ".join(["Winner " + str(i) for i in results.loc[(results["Winner"].isnull()) & (results["Category"]==category)]["Winner Number"]])})')

        if len(missing_req_vals) > 0 or len(missing_opt_vals) == len(CATEGORIES.keys()):
            error_string = "**Error:** "
            if len(missing_req_vals) > 0:
                error_string = error_string + "**Please select names for these required fields:** " + ", ".join(missing_req_vals) + "  \n  \n"
            if len(missing_opt_vals) == len(CATEGORIES.keys()):
                error_string = error_string + "**The following optional fields are empty. At least one of these must be filled.**" + ", ".join(missing_opt_vals) + "  \n  \n"
            elif len(missing_opt_vals) > 0:
                error_string = error_string + "**The following optional fields are also empty. Please check this is intended.**" + ", ".join(missing_opt_vals) + "  \n  \n"
            st.error(error_string[:-6], icon=":material/error:")
        else:
            submission_popup()
