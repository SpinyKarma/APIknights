from src.utils.query import (
    validate_cols,
    IncompleteQueryErr,
    Query,
    SelectQuery
)
from src.utils.formatting import idf
import pytest
from unittest.mock import patch


class Test_validate_cols:
    def test_returns_empty_str_when_passed_empty_string_or_empty_list(self):
        assert validate_cols("") == ""
        assert validate_cols([]) == ""

    def test_if_str_cols_split_into_list_over_comma_and_return(self):
        assert validate_cols("apple, banana") == "apple, banana"

    def test_if_str_cols_split_into_list_disregard_passed_spacing(self):
        assert validate_cols(
            "  apple    ,banana,pear       "
        ) == "apple, banana, pear"

    def test_list_validated_using_idf(self):
        assert validate_cols(
            ["apple 1", "pear 2", "banana 3"]
        ) == '"apple 1", "pear 2", "banana 3"'


class Test_Query:
    def test_Query_takes_table_name_as_arg(self):
        q = Query("banana")
        assert q.table == "banana"

    def test_Query_autovalidates_table_name(self):
        q = Query("banana 1")
        valid = idf("banana 1")
        assert q.table == valid
        assert q.table != "banana 1"

    def test_reading_base_Query_as_str_raises_IncompleteQueryError(self):
        q = Query("banana")
        with pytest.raises(IncompleteQueryErr):
            str(q)

    @patch("src.utils.query.Query.__str__")
    def test_calling_Query_object_returns_str_method(self, m_str):
        q = Query("banana")
        q()
        m_str.assert_called_once()

    def test_select_method_returns_SelectQuery_object_with_self_table(self):
        q = Query("banana 1")
        s = q.select()
        assert isinstance(s, SelectQuery)
        assert s.table == '"banana 1"'

    def test_select_method_takes_optional_col_str_passed_to_SelectQuery(self):
        q = Query("banana 1")
        s = q.select("pears")
        assert s.cols == "pears"


class Test_SelectQuery:
    def test_SelectQuery_extends_Query(self):
        s = SelectQuery("banana")
        assert isinstance(s, Query)

    def test_SelectQuery_takes_optional_cols_arg(self):
        s = SelectQuery("banana", "pears")
        assert s.cols == "pears"

    def test_cols_arg_defaults_to_star(self):
        s = SelectQuery("banana")
        assert s.cols == "*"

    def test_cols_arg_passed_to_validate_cols_before_adding_to_obj(self):
        s = SelectQuery("banana", "pears 1, apples")
        assert s.cols == '"pears 1", apples'

    def test_str_method_returns_select_query_using_table_and_default(self):
        s = SelectQuery("banana 1")
        assert str(s) == 'SELECT * FROM "banana 1";'

    def test_str_method_returns_select_query_using_table_and_passed_cols(self):
        s = SelectQuery("banana", "lemons, pears 1")
        assert str(s) == 'SELECT lemons, "pears 1" FROM banana;'
