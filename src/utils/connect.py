from pg8000.native import Connection
from dotenv import load_dotenv
from os import getenv

load_dotenv()


def connect():
    ''' Return a pg8000 Connection object using the credentials loaded from the
        .env file.
    '''
    user = getenv("PGUSER")
    db = getenv("PGDATABASE")
    password = getenv("PGPASSWORD")
    return Connection(user, database=db, password=password)


def run(query, return_type={}):
    ''' Runs a query to a postgres database and returns the response as a list
        of dictionaies with the column headings as keys and the row data as
        values.

        Args:
            db:
                The connection object to run the query string with.
            query:
                The query string to be run.

        Returns:
            res_dicts:
                The response from the db formatted as a list of dicts, one per
                returned row, with the column headings as the keys.
    '''
    if return_type not in [{}, []]:
        return_type = {}
    with connect() as db:
        res = db.run(str(query))
    if not res:
        res = []
    if not db.columns:
        cols = []
    else:
        cols = [col["name"] for col in db.columns]
    if isinstance(return_type, dict):
        res = [{cols[i]: item[i] for i in range(len(cols))} for item in res]
    elif isinstance(return_type, list):
        res = [cols] + res
    return res
