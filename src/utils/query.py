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


def validate_filters(filters: dict):
    new_dict = {idf(key): lit(filters[key]) for key in filters}
    return new_dict


class IncompleteQueryErr(Exception):
    pass


class Query:
    def __init__(self, table: str):
        self.table = idf(table)

    def __call__(self):
        return self.__str__()

    def __str__(self):
        raise IncompleteQueryErr

    def select(self, cols: str | list = "*"):
        return SelectQuery(self.table, cols)


class SelectQuery(Query):
    def __init__(self, table: str, cols: str | list = "*"):
        super().__init__(table)
        self.cols = validate_cols(cols)
        self.joins = []
        self.wheres = []

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
            self.wheres.append(validate_filters(filters))
        return self

    def __str__(self) -> str:
        query = f"SELECT {self.cols} FROM {self.table}"
        for j in self.joins:
            query += f' {j["j_type"].upper()} JOIN'
            query += f' {j["table"]} ON {j["table"]}.{j["on"]}'
            query += f' = {j.get("table_2", self.table)}.'
            query += j.get("on_2", j["on"])
        if self.wheres != []:
            query += " WHERE "
            and_join = [
                " AND ".join([f"{key} = {w[key]}" for key in w])
                for w in self.wheres
            ]
            or_join = " OR ".join(and_join)
            query += or_join
        query += ";"
        return query
