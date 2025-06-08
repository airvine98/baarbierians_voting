from datetime import datetime
from pathlib import Path

from fpdf import FPDF
from fpdf.fonts import FontFace
from ics import Calendar
import pandas as pd
import requests
from sqlalchemy import create_engine
import yaml


TOTALS_START_DATE = "2024-11-09" # None
TOTALS_END_DATE = "2025-11-08" # None


def get_connection():
    """create the engine to connect to the database

    Returns:
        _engine.Engine: Engine to connect to database
    """
    config = yaml.safe_load(open("config.yml"))
    return create_engine(f"postgresql+psycopg2://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['dbname']}")


def create_pdf_with_tables(folder: str, category_data: dict):
    """create the results pdf

    Args:
        folder (str): name of folder for pdf
        category_data (dict): results data to be displayed
    """
    
    if TOTALS_START_DATE is None and TOTALS_END_DATE is None:
        filename = f"voting_results_all_time.pdf"
        title_text_dates = 'all time'
    elif TOTALS_START_DATE is None and TOTALS_END_DATE is not None:
        filename = f"voting_results_until_{pd.to_datetime(TOTALS_END_DATE).date()}.pdf"
        title_text_dates = f'until {pd.to_datetime(TOTALS_END_DATE).date().strftime("%d/%m/%Y")}'
    elif TOTALS_START_DATE is not None and TOTALS_END_DATE is None:
        filename = f"voting_results_since_{pd.to_datetime(TOTALS_START_DATE).date()}.pdf"
        title_text_dates = f'since {pd.to_datetime(TOTALS_START_DATE).date().strftime("%d/%m/%Y")}'
    else:
        filename = f"voting_results_{pd.to_datetime(TOTALS_START_DATE).date()}_{pd.to_datetime(TOTALS_END_DATE).date()}.pdf"
        title_text_dates = f'{pd.to_datetime(TOTALS_START_DATE).date().strftime("%d/%m/%Y")} - {pd.to_datetime(TOTALS_END_DATE).date().strftime("%d/%m/%Y")}'

    filename = Path(folder).joinpath(filename)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    font_name = "Helvetica"
    pdf.set_font(font_name, size=10)
    headings_style = FontFace(font_name, emphasis="BOLD", fill_color=[170]*3)

    for category, df in category_data.items():
        pdf.add_page()
        pdf.image(Path("images/badge.png"), x=10, y=10, w=30)
        pdf.image(Path("images/badge.png"), x=pdf.w-40, y=10, w=30)
        pdf.set_font(font_name, "B", 14)
        pdf.cell(0, 10, text=f'{category} ({title_text_dates})', align='C')
        pdf.ln(15)
        pdf.set_font(font_name, size=10)

        with pdf.table(headings_style=headings_style, text_align="CENTER", width=100, col_widths=(50, 25, 25)) as table:
            # Create table header
            headers = [x.replace("_", " ").title() for x in df.columns]
            row = table.row()
            for header in headers:
                row.cell(header)

            # Add table rows
            for index, vals in df.iterrows():
                row = table.row()
                for item in vals:
                    row.cell(str(item).replace("’","'"))
    filename.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(filename)
    print(f"\nPDF has been created: {str(filename)}")


if __name__ == "__main__":
    engine = get_connection()

    # Check for missing fridays
    fridays = pd.date_range(
        start=max(pd.to_datetime(TOTALS_START_DATE) if TOTALS_START_DATE is not None else pd.to_datetime("2014-01-01"), pd.to_datetime("2014-01-01")),
        end=min(pd.to_datetime(TOTALS_END_DATE) if TOTALS_END_DATE is not None else datetime.now(), datetime.now()),
        freq="W-FRI"
    ).date

    # Hünenberg holidays calendar https://www.feiertagskalender.ch/export_ical.php?geo=2863
    url = "https://fcal.ch/free/fcal_holidays.ics.php?free_key=FREE-BLUV-S9L9-9WAJ&klasse=3"
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

    # Dictionary to store category data
    category_data = {}

    queries_date_limits = list()
    if TOTALS_START_DATE is not None:
        queries_date_limits.append(f"date >= '{TOTALS_START_DATE}'")
    if TOTALS_END_DATE is not None:
        queries_date_limits.append(f"date < '{TOTALS_END_DATE}'")

    # Get categories and if positive
    categories_query = "SELECT category, AVG(points) >= 0 as positive FROM votes"
    if len(queries_date_limits) > 0:
        categories_query = categories_query + " WHERE " + " AND ".join(queries_date_limits)
    categories_query = categories_query + " GROUP BY category ORDER BY positive DESC, category ASC;"
    categories = pd.read_sql(categories_query, engine).set_index("category").to_dict()["positive"]
    categories["Captain's Performance"] = categories.pop("Captains Performance")

    # Get totals
    for category, positive in categories.items():
        totals_query = f"SELECT winner AS name, COUNT(*) AS votes_won, SUM(points) AS points FROM votes WHERE category = '{category}'"
        if len(queries_date_limits) > 0:
            totals_query = totals_query + " AND " + " AND ".join(queries_date_limits)
        totals_query = totals_query + f" GROUP BY winner ORDER BY points {'DESC' if positive else 'ASC'}, votes_won DESC;"
        totals_query = totals_query.replace("Captain's", "Captains")
        df = pd.read_sql(totals_query, engine)
        category_data[category] = df.head(30)

    # Create PDF
    create_pdf_with_tables(
        f"results",
        category_data
    )
