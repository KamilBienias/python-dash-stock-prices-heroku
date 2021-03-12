import sqlite3
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
# do pobierania cen akcji
import pandas_datareader.data as web


# ticker to 'GOOGL' lub 'MSFT' lub 'AMZN'
def fetch_data_and_safe_to_df_and_database(ticker):
    try:
        df = web.DataReader(name=ticker, data_source='stooq')
        print("Stary index:")
        print(df.index)
        # kolumna Date byla indeksem, wiec trzeba zrobic zeby ona byla kolumna
        # bo inaczej nie jest zapisywana do bazy
        df = df.reset_index()
        print()
        print("Nowy index:")
        print(df.index)
        print()
        print("df.info() =")
        print(df.info())
        print()
        # to nie pomoglo
        # df["Date"] = df["Date"].astype("object")
        print('df["Date"] =')
        print(df["Date"].head())
        dates_as_list = df["Date"].tolist()
        print(dates_as_list[:5])
        list_of_dates_as_strings = []
        for date in dates_as_list:
            # https://thispointer.com/python-how-to-convert-datetime-object-to-string-using-datetime-strftime/
            date_as_string = date.strftime("%Y-%m-%d")
            list_of_dates_as_strings.append(date_as_string)
        print("new_date_as_list =")
        print(list_of_dates_as_strings[:6])
        df["Date"] = list_of_dates_as_strings
        print()
        print("df.info() =")
        print(df.info())
        print()
        print("df =")
        print(df.head())

        # database connection
        connection = sqlite3.connect("stocks_database.sqlite")
        cursor = connection.cursor()
        print("Connection successful")

        # usuwa tabele jesli istniala
        dropTableSql = "DROP TABLE IF EXISTS prices;"
        cursor.execute(dropTableSql)

        # tworzenie tabeli
        createTableSql = """CREATE TABLE IF NOT EXISTS prices(
        Date TEXT,
        Open REAL,
        High REAL,
        Low REAL,
        Close REAL,
        Volume INTEGER
        );"""

        cursor.execute(createTableSql)
        print("Table created")

        # Insert DataFrame records one by one.
        for i, row in df.iterrows():
            # mozna brac kolumny z df lub kolumny z tabeli, czyli moge tez cols_form_df
            sql = """
            INSERT INTO prices (Date, Open, High, Low, Close, Volume) 
            VALUES (?, ?, ?, ?, ?, ?)
            """
            cursor.execute(sql, tuple(row))

        print("Rows inserted to the table")

        # pokazuje date i cene zamkniecia
        retrive_query = "SELECT `Date`, `Close` FROM prices ORDER BY `Date` ASC;"
        # wyswietla wiersz po wierszu
        cursor.execute(retrive_query)
        rows = cursor.fetchall()
        for row in rows:
            print(row)

        print()
        # commiting the connection then closing it.
        connection.commit()
    except Exception as e:
        print(e)
    finally:
        connection.close()
        print("Connection closed")
    return df

# poczatek dash
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# nazwa __name__ to zmienna środowiskowa
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
# potrzebne do heroku
server = app.server

companies_names = {
    'GOOGL': 'Google',
    'MSFT': 'Microsoft',
    'AMZN': 'Amazon'
}

app.layout = html.Div([

    html.H3('Wybierz firmę, aby wyświetlić wykres ceny zamknięcia akcji.'),
    html.H5("Dane ze stooq.pl są za każdym razem zapisywane do bazy sqlite3."),
    html.H5("Po najechaniu myszką wyświetlana jest cena dla danej daty."),
    html.H5("Aby przybliżyć zaznacz wybrany obszar (powrót to symbol 'domek')."),
    dcc.Tabs(
        id='tabs-companies',
        children=[
            dcc.Tab(label='Google', value='GOOGL'),
            dcc.Tab(label='Microsoft', value='MSFT'),
            dcc.Tab(label='Amazon', value='AMZN'),
        ],
        value='GOOGL',
    ),
    # sekcja wynikowa pokazująca wykresy dla wybanej firmy
    html.Div(id='div-result-1'),

    ],   style={
            "color": "darkblue",  # kolor czcionki
            # "fontSize": 18,
            "background-color": "grey",
            "text-align": "center",
            "border": "4px solid Grey",
            # "border-style": "dashed"  # linia przerywana
        }
)

@app.callback(
    Output('div-result-1', 'children'),
    # do funkcji render_content wchodzi ticker.
    # W domyśle Google
    [Input('tabs-companies', 'value')]
)
# w zaleznosci od zakladki bedzie inna zawartosc w id='div-result-1"
def render_content(tab):
    print()
    print("---------------------------------------------------------- Funkcja render_content")
    # pokazuje w konsoli ktora zakladke wybralismy
    print("Wybrana firma jako tab:", tab)

    company_name = tab

    important_columns = ['Date',
                         'Close']

    if tab == company_name:

        # pobieram df dla wybranego tickera i tworze tabele w bazie
        df = fetch_data_and_safe_to_df_and_database(tab)

        # df dla wybranej firmy dla wybranych kolumn
        df_company = df[important_columns]
        # chcę mieć indeksy od 0
        df_company.reset_index(drop=True, inplace=True)

        return html.Div([
            html.H3('Wybrano: ' + companies_names[company_name]),

            dcc.Graph(
                figure={
                    "data": [
                        {
                            "x": df_company["Date"],
                            "y": df_company["Close"],
                            "type": "line",
                            "marker": {
                                "color": "red"
                            },
                            "name": "Cena zamknięcia"
                        },
                    ],
                    'layout': {
                        "title": "Cena zamknięcia akcji w zależności od daty. <br>" +
                        "Ostatnie notowanie z " + str(df_company.head(1)["Date"].values[0]) + " wynosi " + str(df_company.head(1)["Close"].values[0]) + " $",
                        # po najechaniu jest pionowa przerywana linia
                        "hovermode": "x unified"
                    }
                },
                style={
                    "color": "darkblue",  # kolor czcionki
                    # "fontSize": 18,
                    "background-color": "grey",
                    "text-align": "center",
                    "border": "4px solid Black",
                    # "border-style": "dashed"  # linia przerywana
                }
            ),
        ])


# to na localhost
# if __name__ == "__main__":
#     app.run_server(debug=True)