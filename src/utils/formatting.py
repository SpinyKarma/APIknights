from pg8000.native import identifier, literal
import json


def warn(arg):
    print("\033[93m" + arg + "\033[0m")


def err(arg):
    print("\033[91m" + arg + "\033[0m")


def j_d(item):
    ''' Takes an item and returns the json.dumps string version if a dict,
        otherwise does nothing.
    '''
    if isinstance(item, dict):
        return json.dumps(item)
    else:
        return item


def idf(data):
    ''' Takes an item and applies the pg8000 identifier function, for lists
        aplies self recursively so that any sublists also have their
        contents formatted, returning the same data type that was passed.
        Uses j_d to process dicts into strings.
    '''
    if isinstance(data, list):
        return [idf(item) for item in data]
    else:
        return identifier(data)


def lit(data):
    ''' Takes an item and applies the pg8000 literal function, for lists
        aplies self recursively so that any sublists also have their
        contents formatted, returning the same data type that was passed.
        Uses j_d to process dicts into strings.
    '''
    if isinstance(data, list):
        return [lit(item) for item in data]
    else:
        return literal(j_d(data))


def insert_query(table, headings, data, returns=None):
    ''' Constructs an insert query for a single row using the table name,
        column headings, row data and desired return values. SQL injection
        protection is performed in the function so it doesn't need to be done
        before passing to the function.

        Args:
            table:
                The name of the table to insert data into.
            headings:
                A list of column headings for the data to be inserted
                into.
            data:
                A list of row data to be inserted. Must be in matching order
                to the headings list.
            returns (optional):
                A list of column headings to be returned after the query is
                run.

        Returns:
            query:
                The constructed query string.
    '''
    # Convert headings into a SQL injection protected comma separated string
    # whether it was passed as a string or a list
    if isinstance(headings, str):
        headings = [item.strip() for item in headings.split(",")]
    headings = ", ".join(idf(headings))

    # Convert data into a SQL injection protected comma separated string
    # whether it was passed as a string or a list
    if isinstance(data, str):
        data = [item.strip() for item in data.split(",")]
    data = ", ".join(lit(data))

    # Construct the query string
    query_str = f"INSERT INTO {idf(table)} ({headings}) VALUES ({data})"

    # If the returns argument has been passed then SQL format and append
    # to the query string
    if returns:
        if returns == "*":
            query_str += f" RETURNING *"
        else:
            if isinstance(returns, str):
                returns = [item.strip() for item in returns.split(",")]
            returns = ", ".join(idf(returns))
            query_str += f" RETURNING {returns}"

    query_str += ";"
    return query_str


def update_query(table, changes, filters, returns=None):
    ''' Constructs an update query for a single row using the table name,
        changes, filters and desired return values. SQL injection protection
        is performed in the function so it doesn't need to be done before
        passing to the function.

        Args:
            table:
                The name of the table to insert data into.
            changes:
                A list of lists, each being a column heading and a new value
                for that heading. Can also be passed as a dict.
            filters:
                The filters used to determine which rows to alter. Can also
                be passed as a dict.
            returns (optional):
                A list of column headings to be returned after the query is
                run.

        Returns:
            query:
                The constructed query string.  
    '''
    # If changes is a string then split and clean so passed spacing isn't an
    # issue
    if isinstance(changes, str):
        changes = [item.split("=") for item in changes.split(",")]
        changes = [[string.strip() for string in item] for item in changes]
    # If changes is a dict then make each K-V pair a two item sublist
    elif isinstance(changes, dict):
        changes = [[key, changes[key]] for key in changes]
    # Join changes lists into string, using the idf and lit functions to
    # prevent SQL injection
    changes = [idf(item[0])+" = "+lit(item[1]) for item in changes]
    changes = ", ".join(changes)

    # If changes is a string then split and clean so passed spacing isn't an
    # issue
    if isinstance(filters, str):
        filters = [item.split("=") for item in filters.split(",")]
        filters = [[string.strip() for string in item] for item in filters]
    # If filters is a dict then make each K-V pair a two item sublist
    elif isinstance(filters, dict):
        filters = [[key, filters[key]] for key in filters]

    # Join filters lists into string, using the idf and lit functions to
    # prevent SQL injection and j_d to convert any dicts to json strings
    filters = [idf(item[0])+" = "+lit(item[1]) for item in filters]
    filters = " AND ".join(filters)

    # Construct the query string
    query_str = f"UPDATE {idf(table)} SET {changes} WHERE {filters}"

    # If the returns argument has been passed then SQL format and append to
    # the query string
    if returns:
        if returns == "*":
            query_str += f" RETURNING *"
        else:
            if isinstance(returns, str):
                returns = [item.strip() for item in returns.split(",")]
            returns = ", ".join(idf(returns))
            query_str += f" RETURNING {returns}"

    query_str += ";"
    return query_str
