from pg8000.native import Connection
from dotenv import load_dotenv
from os import getenv


load_dotenv()

user = getenv("PGUSER")
password = getenv("PGPASSWORD")


def connect():
    ''' Return a pg8000 Connection object using the credentials loaded from the
        .env file.
    '''
    return Connection(user, database="apiknights", password=password)