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


class IncompleteQueryErr(Exception):
    pass


class Query:
    def __init__(self, table):
        self.table = idf(table)
        self.type = None

    def __call__(self):
        return self.__str__()

    def __str__(self):
        raise IncompleteQueryErr

    def select(self, cols="*"):
        pass

    def insert(self, data):
        pass

    def update(self, changes):
        pass

    def where(self, filters):
        pass

    def returning(self, cols="*"):
        pass


class SelectQuery(Query):
    def __init__(self, table, cols="*"):
        super().__init__(table)
        # cols validation here
        self.joins = []
        self.cols = col_validate(cols)
        self.type = "select"

    def join(self, table1, on, table2=None, other_on=None, join_type="inner"):
        pass

    def __str__(self):
        pass


class InsertQuery(Query):
    def __init__(self, table, data):
        super().__init__(table)
        # data validation here
        self.data = data
        self.type = "insert"


class UpdateQuery(Query):
    def __init__(self, table, changes):
        super().__init__(table)
        # changes validation here
        self.changes = changes
        self.type = "update"


def col_validate(cols):
    pass


def filter_vaidate(filters):
    pass
