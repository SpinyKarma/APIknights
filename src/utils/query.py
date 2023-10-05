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
        return []
    elif isinstance(cols, str):
        cols = [string.strip() for string in cols.split(",")]
    return idf(cols)


def validate_dict(filters: dict):
    new_dict = {idf(key): lit(filters[key]) for key in filters}
    return new_dict


def validate_rows(l: int, rows: list):
    for sub in rows:
        rl = len(sub)
        if rl != l:
            if rl > l:
                gl = "more"
            else:
                gl = "fewer"
            msg = f'At least one row has {gl} entries than the number of '
            msg += 'specified columns.'
            raise MismatchedRowErr(msg)
    return lit(rows)


class IncompleteQueryErr(Exception):
    pass


class MismatchedRowErr(Exception):
    pass


class ImplicitUpdateErr(Exception):
    pass


class Query:
    def __init__(self, table: str):
        self.table = idf(table)

    def __call__(self):
        return self.__str__()

    def __str__(self):
        msg = 'Query class has not been specialised with either "select", '
        msg += '"insert" or "update" methods.'
        raise IncompleteQueryErr(msg)

    def select(self, cols: str | list = "*"):
        return SelectQuery(self.table, cols)

    def insert(self, cols: str | list = [], rows: list = []):
        return InsertQuery(self.table, cols, rows)

    def update(self, changes: dict = None):
        return UpdateQuery(self.table, changes)


class SelectQuery(Query):
    def __init__(self, table: str, cols: str | list = "*"):
        super().__init__(table)
        self.cols = validate_cols(cols)
        self.joins = []
        self.wheres = []

    def select(self, cols="*"):
        self.cols = validate_cols(cols)
        return self

    def join(self, table_1: str, on: str, table_2: str = None,
             on_2: str = None, j_type: str = "inner"):
        if j_type.lower() not in ["inner", "full", "left", "right"]:
            j_type = "inner"
        j = {"table": idf(table_1), "on": idf(on), "j_type": j_type.lower()}
        if table_2:
            j["table_2"] = idf(table_2)
        if on_2:
            j["on_2"] = idf(on_2)
        self.joins.append(j)
        return self

    def where(self, filters: dict):
        if filters != {}:
            self.wheres.append(validate_dict(filters))
        return self

    def __str__(self) -> str:
        query = f"SELECT {', '.join(self.cols)} FROM {self.table}"
        for j in self.joins:
            query += f'\n{j["j_type"].upper()} JOIN'
            query += f' {j["table"]} ON {j["table"]}.{j["on"]}'
            query += f' = {j.get("table_2", self.table)}.'
            query += j.get("on_2", j["on"])
        if self.wheres != []:
            query += "\nWHERE "
            and_join = [
                "\nAND ".join([f"{key} = {w[key]}" for key in w])
                for w in self.wheres
            ]
            or_join = "\nOR ".join(and_join)
            query += or_join
        query += ";"
        return query

    def clear(self, param):
        if param == "join":
            self.joins = []
        elif param == "where":
            self.wheres = []
        return self


class InsertQuery(Query):
    def __init__(self, table: str, cols: str | list = [], rows: list = []):
        super().__init__(table)
        self.cols = validate_cols(cols)
        self.rows = validate_rows(len(self.cols), rows)
        self.returns = None

    def row(self, row_data):
        self.rows += validate_rows(len(self.cols), row_data)
        return self

    def insert(self, cols: str | list = [], rows: list = []):
        self.cols = validate_cols(cols)
        self.rows = validate_rows(len(self.cols), rows)
        return self

    def returning(self, returns=["*"]):
        self.returns = validate_cols(returns)
        return self

    def clear(self, param):
        if param == "returning":
            self.returns = None
        elif param == "insert":
            self.rows = []
            self.cols = []
        return self

    def __str__(self):
        if self.rows == [] or self.cols == []:
            msg = 'Information for both cols and rows is needed for a valid '
            msg += 'insert query.'
            raise IncompleteQueryErr(msg)
        query = f"INSERT INTO {self.table}"
        query += f"\n({', '.join(self.cols)})"
        query += "\nVALUES"
        joined_rows = [', '.join(row) for row in self.rows]
        compiled_rows = "\n("+"),\n(".join(joined_rows)+")"
        query += compiled_rows
        if self.returns:
            query += f"\nRETURNING {', '.join(self.returns)}"
        query += ";"
        return query


class UpdateQuery(Query):
    def __init__(self, table, changes=None):
        super().__init__(table)
        self.changes = validate_dict(changes) if changes else {}
        self.wheres = []
        self.no_filter = False
        self.returns = None

    def update(self, changes=None):
        self.changes = validate_dict(changes) if changes else {}
        return self

    def where(self, filters):
        if filters == "*":
            self.no_filter = True
        elif filters != {}:
            self.wheres.append(validate_dict(filters))
            self.no_filter = False
        return self

    def returning(self, cols="*"):
        self.returns = validate_cols(cols)
        return self

    def clear(self, param):
        if param == "update":
            self.changes = {}
        elif param == "where":
            self.wheres = []
            self.no_filter = False
        elif param == "returning":
            self.returns = None
        return self

    def __str__(self):
        if self.changes == {}:
            msg = 'Information for changes to make is needed for a valid '
            msg += 'update query.'
            raise IncompleteQueryErr(msg)
        if not self.no_filter and self.wheres == []:
            msg = 'No filters have been set. All rows will be updated. If '
            msg += 'this is your intent then pass "*" to the where method to '
            msg += 'explicitly declare so.'
            raise ImplicitUpdateErr(msg)
        query = f"UPDATE {self.table}\nSET\n"
        joined_changes = ",\n".join([
            f"{key} = {self.changes[key]}" for key in self.changes
        ])
        query += joined_changes
        if not self.no_filter:
            query += "\nWHERE "
            and_join = [
                "\nAND ".join([f"{key} = {w[key]}" for key in w])
                for w in self.wheres
            ]
            or_join = "\nOR ".join(and_join)
            query += or_join
        if self.returns:
            query += f"\nRETURNING {', '.join(self.returns)}"
        query += ";"
        return query
