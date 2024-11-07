from fpdf import FPDF
import pandas as pd
from sqlalchemy import create_engine
import yaml
from ics import Calendar
import requests
import os

TOTALS_START_DATE = "2023-11-11"

# Function to get database connection
def get_connection():
    config = yaml.safe_load(open("config.yml"))
    return create_engine(f"postgresql+psycopg2://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['dbname']}")

# Simplified function to create a PDF with tables
def create_pdf_with_tables(filename, category_data):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=10)

    for category, df in category_data.items():
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, txt=category, ln=True, align='C')
        pdf.set_font("Arial", size=10)

        # Create table header
        headers = ['Name'] + list(df.columns)
        pdf.set_fill_color(200, 200, 200)
        for header in headers:
            pdf.cell(40, 8, header, border=1, fill=True, align='C')
        pdf.ln()

        # Add table rows
        for index, row in df.iterrows():
            pdf.cell(40, 8, str(index), border=1, align='C')
            for item in row:
                pdf.cell(40, 8, str(item), border=1, align='C')
            pdf.ln()

    pdf.output(filename)

if __name__ == "__main__":
    engine = get_connection()

    # Check for missing fridays
    fridays = pd.date_range(
        start=pd.to_datetime(TOTALS_START_DATE),
        end=pd.Timestamp.today(),
        freq="W-FRI"
    ).date

    # Hünenberg holidays calendar https://www.feiertagskalender.ch/export_ical.php?geo=2863
    url = "https://fcal.ch/privat/fcal_holidays.ics.php?hl=de&klasse=3&geo=2863"
    calendar = Calendar(requests.get(url).text)
    holidays = [x.begin.date() for x in list(calendar.events)]

    fridays_excl_holidays = [date for date in fridays if date not in holidays]

    dates_query = f"SELECT DISTINCT date FROM votes ORDER BY date ASC;"
    dates = pd.read_sql(dates_query, engine)["date"].to_list()

    missing_fridays = [date.strftime("%d.%m.%Y") for date in fridays_excl_holidays if date not in dates]

    if len(missing_fridays) > 0:
        print("\nMissing Fridays:\n" + "\n".join(missing_fridays))
    else:
        print(f"\nVotes have been submitted for every Friday since {TOTALS_START_DATE}.")

    # Define categories (and if positive)
    categories = {
        "Goal of the Night": True,
        "Save of the Night": True,
        "Skill Moment": True,
        "Worst Tackle": False,
        "Duffer": False,
        "Drama Queen": False,
        "Greedy Bastard": False,
        "Golden Goal": True,
        "Captain's Performance": True
    }

    # Dictionary to store category data
    category_data = {}

    for category, positive in categories.items():
        totals_query = f"SELECT * FROM {category.lower().replace(' ', '_')} ORDER BY points {'DESC' if positive else 'ASC'}, votes_won DESC;"
        totals_query = totals_query.replace("n's", "ns")
        df = pd.read_sql(totals_query, engine, index_col="name")
        category_data[category] = df.head(30)  # Add top 10 to the dictionary

    # Create PDF
    create_pdf_with_tables("category_results.pdf", category_data)
    print("PDF has been created: category_results.pdf")
