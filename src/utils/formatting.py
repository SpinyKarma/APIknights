from pg8000.native import identifier, literal
import json


class MismatchKeysErr(Exception):
    pass


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
    '''
    if isinstance(data, list):
        return [idf(item) for item in data]
    elif data == "*":
        return data
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


def select_query(table, cols="*", filters={}):
    table = idf(table)
    if isinstance(cols, str):
        if cols.split(", ")[0] != cols:
            cols = cols.split(", ")
    cols = idf(cols)
    if isinstance(cols, list):
        cols = ", ".join(cols)
    query = f"SELECT {cols} FROM {table}"
    filters = " AND ".join(
        [idf(key)+" = "+lit(filters[key]) for key in filters]
    )
    if filters:
        query += f" WHERE {filters}"
    query += ";"
    return query


def insert_query(table, row_dicts, returns=None):
    if isinstance(row_dicts, dict):
        row_dicts = [row_dicts]
    if len(row_dicts) > 1:
        key_set = {tuple(d.keys()) for d in row_dicts}
        if len(key_set) > 1:
            raise MismatchKeysErr
    table = idf(table)
    cols = [idf(key) for key in row_dicts[0]]
    cols = "(" + ", ".join(cols) + ")"
    data = "("
    rows = [", ".join([lit(row[key]) for key in row]) for row in row_dicts]
    data += "), (".join(rows)
    data += ")"
    query = f"INSERT INTO {table} {cols} VALUES {data}"
    if returns:
        if isinstance(returns, str):
            if returns.split(", ")[0] != returns:
                returns = returns.split(", ")
        returns = idf(returns)
        if isinstance(returns, list):
            returns = ", ".join(returns)
        query += f" RETURNING {returns}"
    query += ";"
    return query


def update_query(table, changes, filters={}, returns=None):
    table = idf(table)
    changes = ", ".join([idf(key)+" = "+lit(changes[key]) for key in changes])
    filters = " AND ".join(
        [idf(key)+" = "+lit(filters[key]) for key in filters]
    )
    query = f"UPDATE {table} SET {changes}"
    if filters:
        query += f" WHERE {filters}"
    if returns:
        if isinstance(returns, str):
            if returns.split(", ")[0] != returns:
                returns = returns.split(", ")
        returns = idf(returns)
        if isinstance(returns, list):
            returns = ", ".join(returns)
        query += f" RETURNING {returns}"
    query += ";"
    return query
