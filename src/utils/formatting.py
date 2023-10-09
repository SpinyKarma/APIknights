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
    elif isinstance(data, str) and data[0] == '"' and data[-1] == '"':
        return identifier(data[1:-1])
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
    elif isinstance(data, str) and data[0] == "'" and data[-1] == "'":
        return lit(data[1:-1])
    elif isinstance(data, str):
        return literal(data.replace("''", "'"))
    else:
        return literal(j_d(data))
