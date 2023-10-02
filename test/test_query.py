from src.utils.query import (
    validate_cols,
    IncompleteQueryErr,
    Query,
    SelectQuery,
    validate_filters
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


class Test_validate_filters:
    def test_returns_empty_when_passed_empty(self):
        assert {} == validate_filters({})

    def test_validates_keys_and_vals_before_return(self):
        filter_dict = {"lemon 1": "lime's"}
        validated_dict = {'"lemon 1"': "'lime''s'"}
        assert validated_dict == validate_filters(filter_dict)


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

    def test_join_method_takes_table_col_type_stores_in_joins_as_dict(self):
        s = SelectQuery("banana").join("lemon", "orange", j_type="inner")
        assert {"table": "lemon", "on": "orange", "j_type": "inner"} in s.joins

    def test_join_type_optional_defaults_to_inner(self):
        s = SelectQuery("banana").join("lemon", "orange")
        assert {"table": "lemon", "on": "orange", "j_type": "inner"} in s.joins

    def test_join_if_type_not_outer_left_right_then_set_to_inner(self):
        s_o = SelectQuery("banana").join("lemon", "orange", j_type="full")
        s_l = SelectQuery("banana").join("lemon", "orange", j_type="left")
        s_r = SelectQuery("banana").join("lemon", "orange", j_type="right")
        s_b = SelectQuery("banana").join("lemon", "orange", j_type="banana")
        assert {
            "table": "lemon", "on": "orange", "j_type": "full"
        } in s_o.joins
        assert {
            "table": "lemon", "on": "orange", "j_type": "left"
        } in s_l.joins
        assert {
            "table": "lemon", "on": "orange", "j_type": "right"
        } in s_r.joins
        assert {
            "table": "lemon", "on": "orange", "j_type": "inner"
        } in s_b.joins

    def test_join_j_type_case_insensitive(self):
        s = SelectQuery("banana").join("lemon", "orange", j_type="FuLl")
        assert {"table": "lemon", "on": "orange", "j_type": "full"} in s.joins

    def test_join_method_takes_second_table_arg_if_not_joined_on_self(self):
        s = SelectQuery("banana").join("lemon", "orange", table_2="apple")
        assert {
            "table": "lemon",
            "on": "orange",
            "table_2": "apple",
            "j_type": "inner"
        } in s.joins

    def test_join_method_takes_second_col_arg_if_not_joined_on_same_col(self):
        s = SelectQuery("banana").join("lemon", "orange", on_2="lime")
        assert {
            "table": "lemon",
            "on": "orange",
            "on_2": "lime",
            "j_type": "inner"
        } in s.joins

    def test_join_validates_all_args_before_adding(self):
        s = SelectQuery("banana").join(
            "lemon 2",
            "orange 3",
            table_2="apple 4",
            on_2="lime 5"
        )
        assert {
            "table": '"lemon 2"',
            "on": '"orange 3"',
            "table_2": '"apple 4"',
            "on_2": '"lime 5"',
            "j_type": "inner"
        } in s.joins

    def test_join_can_be_chained_to_add_to_list(self):
        s = SelectQuery("banana").join("one", "two").join("three", "four")
        assert {"table": "one", "on": "two", "j_type": "inner"} in s.joins
        assert {"table": "three", "on": "four", "j_type": "inner"} in s.joins

    def test_str_method_appends_basic_join_to_query(self):
        s = SelectQuery("banana").join("one", "two")
        expected = 'SELECT * FROM banana '
        expected += 'INNER JOIN one ON one.two = banana.two;'
        assert str(s) == expected

    def test_str_method_appends_join_using_table_2(self):
        s = SelectQuery("banana").join("one", "two", table_2="three")
        expected = 'SELECT * FROM banana '
        expected += 'INNER JOIN one ON one.two = three.two;'
        assert str(s) == expected

    def test_str_method_appends_join_using_on_2(self):
        s = SelectQuery("banana").join("one", "two", on_2="four")
        expected = 'SELECT * FROM banana '
        expected += 'INNER JOIN one ON one.two = banana.four;'
        assert str(s) == expected

    def test_str_method_changes_join_type_using_j_type(self):
        s = SelectQuery("banana").join("one", "two", j_type="full")
        expected = 'SELECT * FROM banana '
        expected += 'FULL JOIN one ON one.two = banana.two;'
        assert str(s) == expected

    def test_str_method_appends_arbitrary_join(self):
        s = SelectQuery("banana").join(
            "one", "two", table_2="three", on_2="four", j_type="left"
        )
        expected = 'SELECT * FROM banana '
        expected += 'LEFT JOIN one ON one.two = three.four;'
        assert str(s) == expected

    def test_str_method_appends_all_joins_in_list(self):
        s = SelectQuery("banana").join(
            "one", "two", table_2="three", j_type="left"
        ).join(
            "alpha", "beta", on_2="gamma", j_type="full"
        )
        expected = 'SELECT * FROM banana '
        expected += 'LEFT JOIN one ON one.two = three.two '
        expected += 'FULL JOIN alpha ON alpha.beta = banana.gamma;'
        assert str(s) == expected

    def test_where_appends_dict_to_self_wheres_list(self):
        s = SelectQuery("banana")
        assert len(s.wheres) == 0
        s.where({"apple": "orange"})
        assert len(s.wheres) == 1

    def test_does_not_append_if_passed_empty_dict(self):
        s = SelectQuery("banana")
        assert len(s.wheres) == 0
        s.where({})
        assert len(s.wheres) == 0

    def test_passes_dict_to_validate_filters_before_appending(self):
        filter_dict = {"apple": "orange"}
        validated_dict = validate_filters(filter_dict)
        s = SelectQuery("banana").where(filter_dict)
        assert s.wheres == [validated_dict]

    def test_succesive_calls_add_new_dicts_to_list(self):
        filter_dict = {"apple": "orange"}
        validated_dict = validate_filters(filter_dict)
        s = SelectQuery("banana").where(filter_dict).where(filter_dict)
        assert s.wheres == [validated_dict, validated_dict]

    def test_str_method_appends_single_where_clause_to_query(self):
        s = SelectQuery("banana").where({"apple": "orange"})
        assert str(s) == "SELECT * FROM banana WHERE apple = 'orange';"

    def test_str_method_appends_extra_keys_in_filter_with_and(self):
        s = SelectQuery("banana").where({"apple": "orange", "lemon": "lime"})
        expected = "SELECT * FROM banana WHERE apple = 'orange' "
        expected += "AND lemon = 'lime';"
        assert str(s) == expected

    def test_str_method_appends_extra_filter_dicts_with_or(self):
        s = SelectQuery("banana")
        s.where({"apple": "orange"})
        s.where({"lemon": "lime"})
        expected = "SELECT * FROM banana WHERE apple = 'orange' "
        expected += "OR lemon = 'lime';"
        assert str(s) == expected

    def test_str_method_appends_arbitrary_dicts(self):
        s = SelectQuery("banana")
        s.where({"apple": "orange", "one": "two"})
        s.where({"lemon": "lime"})
        s.where({"alpha": "beta"})
        expected = "SELECT * FROM banana "
        expected += "WHERE apple = 'orange' AND one = 'two' "
        expected += "OR lemon = 'lime' "
        expected += "OR alpha = 'beta';"
        assert str(s) == expected

    def test_str_method_appends_where_clause_after_join_clause(self):
        s = SelectQuery("banana")
        s.where({"apple": "orange"})
        s.join("lemon", "lime")
        expected = "SELECT * FROM banana "
        expected += "INNER JOIN lemon ON lemon.lime = banana.lime "
        expected += "WHERE apple = 'orange';"
        assert str(s) == expected
