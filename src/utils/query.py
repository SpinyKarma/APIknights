from src.utils.formatting import idf, lit
from copy import deepcopy
''' __init__:
        args:
            table:
                name of the table to query

    __str__:
        returns:
            the valid sql query string if self.type not None
        raises:
            IncompleteQueryErr if self.type == None

    __call__:
        returns self.__str__()

    select:
        args:
            cols:
                list of col headings to select, defaults to *
        returns:
            SelectQuery obj with self instance values

    insert:
        args:
            data:
                dict or list of dicts (one per row) with cols and
                row data as KV
        returns:
            InsertQuery obj with self instance values
        raises:
            MismatchKeysError if data dicts don't have the same key set

    update:
        args:
            changes:
                dict of cols and values to set as KV
        returns:
            UpdateQuery obj with self instance values

    where: (Select and Update only)
        args:
            filters: dict of col headings and desired values as KV
        returns:
            self

    join: (Select only)
        args:
            table:
                name of other table to join
            on:
                self col to perform join on
            other_on:
                other table's col to join on, defaults to self's on
            type:
                determines type of join, defaults to inner if one of
                ["inner", "left", "right", "outer"] not provided

    returning: (Insert and Update only):
        args:
            cols:
                list of cols to return from the query, defaults to *
        returns:
            self

'''


def validate_cols(cols: str | list):
    if cols == "":
        return cols
    elif isinstance(cols, str):
        cols = [string.strip() for string in cols.split(",")]
    return ", ".join(idf(cols))


class IncompleteQueryErr(Exception):
    pass


class Query:
    def __init__(self, table: str):
        self.table = idf(table)

    def __call__(self):
        return self.__str__()

    def __str__(self):
        raise IncompleteQueryErr

    def select(self, cols: str = "*"):
        return SelectQuery(self.table, cols)


class SelectQuery(Query):
    def __init__(self, table: str, cols: str | list = "*"):
        super().__init__(table)
        self.joins = []
        self.cols = validate_cols(cols)

    def join(self, table1, on, table2=None, other_on=None, join_type="inner"):
        pass

    def __str__(self):
        query = f"SELECT {self.cols} FROM {self.table};"
        return query
