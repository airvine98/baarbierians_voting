from pathlib import Path

from fpdf import FPDF
from fpdf.fonts import FontFace
from ics import Calendar
import pandas as pd
import requests
from sqlalchemy import create_engine
import yaml


TOTALS_START_DATE = "2023-11-11"
TOTALS_END_DATE = "2024-11-09"


def get_connection():
    """create the engine to connect to the database

    Returns:
        _engine.Engine: Engine to connect to database
    """
    config = yaml.safe_load(open("config.yml"))
    return create_engine(f"postgresql+psycopg2://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['dbname']}")


def create_pdf_with_tables(filename: str, category_data: dict):
    """create the results pdf

    Args:
        filename (str): name of file for pdf
        category_data (dict): results data to be displayed
    """
    filename = Path(filename)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Helvetica", size=10)
    headings_style = FontFace(emphasis="BOLD", fill_color=[170]*3)

    for category, df in category_data.items():
        pdf.add_page()
        pdf.image(Path("images/badge.png"), x=10, y=10, w=30)
        pdf.image(Path("images/badge.png"), x=pdf.w-40, y=10, w=30)
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, text=f'{category} ({pd.to_datetime(TOTALS_START_DATE).date().strftime("%d/%m/%Y")} - {pd.to_datetime(TOTALS_END_DATE).date().strftime("%d/%m/%Y")})', align='C')
        pdf.ln(15)
        pdf.set_font("Helvetica", size=10)

        with pdf.table(headings_style=headings_style, text_align="CENTER", width=100, col_widths=(50, 25, 25)) as table:
            # Create table header
            headers = ['Name'] + [x.replace("_", " ").title() for x in df.columns]
            row = table.row()
            for header in headers:
                row.cell(header)

            # Add table rows
            for index, vals in df.iterrows():
                row = table.row()
                row.cell(str(index))
                for item in vals:
                    row.cell(str(item))
    filename.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(filename)
    print(f"PDF has been created: {str(filename)}")


if __name__ == "__main__":
    engine = get_connection()

    # Check for missing fridays
    fridays = pd.date_range(
        start=pd.to_datetime(TOTALS_START_DATE),
        end=pd.to_datetime(TOTALS_END_DATE),
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
    create_pdf_with_tables(
        f"results/voting_results_{pd.to_datetime(TOTALS_END_DATE).year}.pdf",
        category_data
    )
