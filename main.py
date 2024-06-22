import streamlit as st
import pandas as pd
from datetime import datetime
import psycopg2
import os

st.title('Baarbierians Voting Form')
st.write('Fill out the date of the voting, the name of the voting organiser and the results of each category including whether the winner was in the pub or not. After submitting the form, a message will appear at the bottom of the page which can be posted in the Whatsapp group.')

## Get database connection
def get_connection():
    return psycopg2.connect(
        dbname=os.getenv('dbname'),
        user=os.getenv('user'), 
        password=os.getenv('password'), 
        host=os.getenv('host'),
    )


# Define categories
positive_categories = ['Goal of the night', 'Save of the night', 'Skill Moment', 'Golden Goal', 'Captain\'s Performance']
negative_categories = ['Duffer', 'Worst Tackle', 'Drama Queen', 'Greedy Bastard']
all_categories = positive_categories + negative_categories

# Define organisers
# Should dynamically update if an entry is submitted in the "other" field
organisers = ['Andrew', 'Alistair', 'Andy', 'Scott', 'Mark H', 'Mark B','Gary', 'Panu', 'Carlo', 'Simon']
organisers.sort()
organisers.append('Other')

# Define players
# Should dynamically update if an entry is submitted in the "other" field
players = ['Andrew', 'Alistair', 'Andy', 'Scott', 'Mark H', 'Mark B','Gary', 'Panu', 'Carlo', 'Simon']

# Date input outside the form
date = st.date_input('Date', datetime.now())

# Voting organiser selection outside the form
filled_by = st.selectbox('Voting Organiser', organisers, index=organisers.index('Andrew'))

# Conditional input for 'Other' organiser
if filled_by == 'Other':
    filled_by = st.text_input('Enter organiser name')


with st.form('voting_form'):
    
    form_data = []
    
    for category in all_categories:
        winner = st.selectbox(f'Winner of {category}', players)
        if winner == 'Add New Player':
            winner = st.text_input(f'Enter new player name for {category}')
            players.add(winner)
        
        in_pub = st.checkbox(f'Was winner in the pub for {category}?')

        
        if category in positive_categories:
            points = 1
        else:
            points = -1
        
        if not in_pub:
            points -= 1

        
        form_data.append([date, filled_by, category, winner, in_pub, points])
    
    submitted = st.form_submit_button('Submit')
