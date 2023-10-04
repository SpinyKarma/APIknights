from src.utils.query import (
    validate_cols,
    validate_filters,
    validate_data,
    IncompleteQueryErr,
    MismatchedRowError,
    Query,
    SelectQuery,
    InsertQuery
)
from src.utils.formatting import idf, lit
import pytest
from unittest.mock import patch


class Test_validate_cols:
    def test_returns_empty_list_when_passed_empty_string_or_empty_list(self):
        assert validate_cols("") == []
        assert validate_cols([]) == []

    def test_if_str_cols_split_into_list_over_comma_and_return(self):
        assert validate_cols("apple, banana") == ["apple", "banana"]

    def test_if_str_cols_split_into_list_disregard_passed_spacing(self):
        assert validate_cols(
            "  apple    ,banana,pear       "
        ) == ["apple", "banana", "pear"]

    def test_list_validated_using_idf(self):
        assert validate_cols(
            ["apple 1", "pear 2", "banana 3"]
        ) == ['"apple 1"', '"pear 2"', '"banana 3"']


class Test_validate_filters:
    def test_returns_empty_when_passed_empty(self):
        assert {} == validate_filters({})

    def test_validates_keys_and_vals_before_return(self):
        filter_dict = {"lemon 1": "lime's"}
        validated_dict = {'"lemon 1"': "'lime''s'"}
        assert validated_dict == validate_filters(filter_dict)


class Test_validate_data:
    def test_returns_empty_list_when_passed_empty_list(self):
        assert validate_data(0, []) == []

    def test_raise_MismatchedRowError_if_len_any_sublist_not_passed_l(self):
        validate_data(2, [[1, 2], [3, 4]])
        with pytest.raises(MismatchedRowError):
            validate_data(2, [[1, 2], [3]])

    def test_validates_list_and_sublists_with_lit(self):
        assert validate_data(1, [["apple"]]) == lit([["apple"]])


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

    def test_select_method_takes_optional_col_list_passed_to_SelectQuery(self):
        q = Query("banana 1")
        s = q.select(["pears"])
        assert s.cols == ["pears"]

    def test_select_method_col_can_be_passed_as_comma_sep_string(self):
        q = Query("banana 1")
        s = q.select("pears, apple")
        assert s.cols == ["pears", "apple"]

    def test_select_method_col_arg_defaults_to_star(self):
        q = Query("banana 1")
        s = q.select()
        assert s.cols == ["*"]

    def test_insert_method_returns_InsertQuery_object_with_self_table(self):
        q = Query("banana")
        i = q.insert()
        assert isinstance(i, InsertQuery)
        assert i.table == 'banana'

    def test_insert_method_takes_optional_col_list_passed_to_InsertQuery(self):
        q = Query("banana 1")
        i = q.insert(["pears"])
        assert i.cols == ["pears"]

    def test_insert_method_col_can_be_passed_as_comma_sep_string(self):
        q = Query("banana 1")
        i = q.insert("pears, apple")
        assert i.cols == ["pears", "apple"]

    def test_insert_method_col_arg_defaults_to_empty_list(self):
        q = Query("banana 1")
        i = q.insert()
        assert i.cols == []

    def test_insert_method_takes_optional_row_list_passed_to_InsertQuery(self):
        q = Query("banana 1")
        i = q.insert(["lime"], [["lemon"]])
        assert i.rows == [["'lemon'"]]

    def test_insert_method_row_arg_defaults_to_empty_list(self):
        q = Query("banana 1")
        i = q.insert()
        assert i.rows == []


class Test_SelectQuery:
    def test_SelectQuery_extends_Query(self):
        s = SelectQuery("banana")
        assert isinstance(s, Query)

    def test_SelectQuery_takes_optional_cols_arg(self):
        s = SelectQuery("banana", "pears")
        assert s.cols == ["pears"]

    def test_cols_arg_defaults_to_star(self):
        s = SelectQuery("banana")
        assert s.cols == ["*"]

    def test_select_method_overwrites_self_cols_with_passed_arg(self):
        s = SelectQuery("banana", "pears")
        s.select("lemon 2")
        assert s.cols == ['"lemon 2"']

    def test_cols_arg_passed_to_validate_cols_before_adding_to_obj(self):
        s = SelectQuery("banana", "pears 1, apples")
        assert s.cols == ['"pears 1"', 'apples']

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
        expected = 'SELECT * FROM banana'
        expected += '\nINNER JOIN one ON one.two = banana.two;'
        assert str(s) == expected

    def test_str_method_appends_join_using_table_2(self):
        s = SelectQuery("banana").join("one", "two", table_2="three")
        expected = 'SELECT * FROM banana'
        expected += '\nINNER JOIN one ON one.two = three.two;'
        assert str(s) == expected

    def test_str_method_appends_join_using_on_2(self):
        s = SelectQuery("banana").join("one", "two", on_2="four")
        expected = 'SELECT * FROM banana'
        expected += '\nINNER JOIN one ON one.two = banana.four;'
        assert str(s) == expected

    def test_str_method_changes_join_type_using_j_type(self):
        s = SelectQuery("banana").join("one", "two", j_type="full")
        expected = 'SELECT * FROM banana'
        expected += '\nFULL JOIN one ON one.two = banana.two;'
        assert str(s) == expected

    def test_str_method_appends_arbitrary_join(self):
        s = SelectQuery("banana").join(
            "one", "two", table_2="three", on_2="four", j_type="left"
        )
        expected = 'SELECT * FROM banana'
        expected += '\nLEFT JOIN one ON one.two = three.four;'
        assert str(s) == expected

    def test_str_method_appends_all_joins_in_list(self):
        s = SelectQuery("banana").join(
            "one", "two", table_2="three", j_type="left"
        ).join(
            "alpha", "beta", on_2="gamma", j_type="full"
        )
        expected = 'SELECT * FROM banana'
        expected += '\nLEFT JOIN one ON one.two = three.two'
        expected += '\nFULL JOIN alpha ON alpha.beta = banana.gamma;'
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
        assert str(s) == "SELECT * FROM banana\nWHERE apple = 'orange';"

    def test_str_method_appends_extra_keys_in_filter_with_and(self):
        s = SelectQuery("banana").where({"apple": "orange", "lemon": "lime"})
        expected = "SELECT * FROM banana"
        expected += "\nWHERE apple = 'orange' AND lemon = 'lime';"
        assert str(s) == expected

    def test_str_method_appends_extra_filter_dicts_with_or(self):
        s = SelectQuery("banana")
        s.where({"apple": "orange"})
        s.where({"lemon": "lime"})
        expected = "SELECT * FROM banana"
        expected += "\nWHERE apple = 'orange' OR lemon = 'lime';"
        assert str(s) == expected

    def test_str_method_appends_arbitrary_dicts(self):
        s = SelectQuery("banana")
        s.where({"apple": "orange", "one": "two"})
        s.where({"lemon": "lime"})
        s.where({"alpha": "beta", "gamma": "delta"})
        expected = "SELECT * FROM banana"
        expected += "\nWHERE apple = 'orange' AND one = 'two' "
        expected += "OR lemon = 'lime' "
        expected += "OR alpha = 'beta' AND gamma = 'delta';"
        assert str(s) == expected

    def test_str_method_appends_where_clause_after_join_clause(self):
        s = SelectQuery("banana")
        s.where({"apple": "orange"})
        s.join("lemon", "lime")
        expected = "SELECT * FROM banana"
        expected += "\nINNER JOIN lemon ON lemon.lime = banana.lime"
        expected += "\nWHERE apple = 'orange';"
        assert str(s) == expected

    def test_clear_method_clears_joins_list_if_passed_string_join(self):
        s = SelectQuery("banana")
        s.join("lemon", "lime")
        s.clear("join")
        assert s.joins == []

    def test_clear_method_clears_wheres_list_if_passed_string_where(self):
        s = SelectQuery("banana")
        s.where({"lemon": "lime"})
        s.clear("where")
        assert s.wheres == []


class Test_InsertQuery:
    def test_InsertQuery_extends_Query(self):
        i = InsertQuery("banana")
        assert isinstance(i, Query)

    def test_InsertQuery_takes_optional_cols_list(self):
        i = InsertQuery("banana", ["pears"])
        assert i.cols == ["pears"]

    def test_cols_can_also_be_passed_as_comma_sep_string(self):
        i = InsertQuery("banana", "pears, apples")
        assert i.cols == ["pears", "apples"]

    def test_cols_validated_with_idf_before_setting_to_instance(self):
        i = InsertQuery("banana", ["pears 1"])
        assert i.cols == ['"pears 1"']

    def test_cols_arg_defaults_to_empty_list(self):
        i = InsertQuery("banana")
        assert i.cols == []

    def test_rows_arg_defaults_to_empty_list(self):
        i = InsertQuery("banana")
        assert i.rows == []

    @patch("src.utils.query.validate_data")
    def test_InsertQuery_rows_list_of_list_uses_validate_data(self, m_val):
        m_val.return_value = [["'lemon'"]]
        i = InsertQuery("banana", ["pears"], [["lemon"]])
        m_val.assert_called_with(len(["pears"]), [["lemon"]])
        assert i.rows == [["'lemon'"]]

    def test_if_rows_sublist_not_len_of_cols_raise_MismatchedRowError(self):
        with pytest.raises(MismatchedRowError):
            InsertQuery("banana", ["pears"], [["orange"], ["apple", "pear"]])

    @patch("src.utils.query.validate_data")
    def test_row_method_adds_sublists_to_rows_using_validate_data(self, m_val):
        m_val.side_effect = [[["'lemon'"]], [["'apple'"]]]
        i = InsertQuery("banana", ["pears"], [["lemon"]])
        i.row([["apple"]])
        m_val.assert_called_with(len(["pears"]), [["apple"]])
        assert i.rows == [["'lemon'"], ["'apple'"]]

    def test_insert_method_overwrites_init_params_using_same_validation(self):
        i = InsertQuery("banana", ["pears"], [["lemon"]])
        i.insert(["apples"], [["orange"]])
        assert i.cols == ["apples"]
        assert i.rows == [["'orange'"]]

    def test_str_method_raises_IncompleteQueryErr_if_no_row_or_col_data(self):
        i = InsertQuery("banana")
        with pytest.raises(IncompleteQueryErr):
            str(i)

    def test_str_method_assembles_insert_query_one_row_one_col(self):
        i = InsertQuery("banana", ["pears"], [["lemon"]])
        expected = "INSERT INTO banana"
        expected += "\n(pears)"
        expected += "\nVALUES"
        expected += "\n('lemon');"
        assert str(i) == expected

    def test_str_method_assembles_insert_query_one_row_multi_col(self):
        i = InsertQuery("banana", ["pears", "apples"], [["lemon", "lime"]])
        expected = "INSERT INTO banana"
        expected += "\n(pears, apples)"
        expected += "\nVALUES"
        expected += "\n('lemon', 'lime');"
        assert str(i) == expected

    def test_str_method_assembles_insert_query_multi_row_one_col(self):
        i = InsertQuery("banana", ["pears"], [["lemon"], ["lime"]])
        expected = "INSERT INTO banana"
        expected += "\n(pears)"
        expected += "\nVALUES"
        expected += "\n('lemon'),"
        expected += "\n('lime');"
        assert str(i) == expected

    def test_str_method_assembles_insert_query_multi_row_multi_col(self):
        i = InsertQuery(
            "banana",
            ["pears", "apples"],
            [["lemon", "lime"], ["orange", "grape"]]
        )
        expected = "INSERT INTO banana"
        expected += "\n(pears, apples)"
        expected += "\nVALUES"
        expected += "\n('lemon', 'lime'),"
        expected += "\n('orange', 'grape');"
        assert str(i) == expected

    def test_returning_method_takes_returns_list(self):
        i = InsertQuery("banana")
        i.returning(["lemon"])
        assert i.returns == ["lemon"]

    def test_returns_can_also_be_passed_as_comma_sep_string(self):
        i = InsertQuery("banana")
        i.returning("pears, apples")
        assert i.returns == ["pears", "apples"]

    def test_returns_validated_with_idf_before_setting_to_instance(self):
        i = InsertQuery("banana")
        i.returning(["pears 1"])
        assert i.returns == ['"pears 1"']

    def test_returns_arg_defaults_to_star(self):
        i = InsertQuery("banana")
        i.returning()
        assert i.returns == ["*"]

    def test_str_method_appends_return_clause_if_returns_not_None(self):
        i = InsertQuery("banana", ["pears"], [["lemon"]]).returning("apple")
        expected = "INSERT INTO banana"
        expected += "\n(pears)"
        expected += "\nVALUES"
        expected += "\n('lemon')"
        expected += "\nRETURNING apple;"
        assert str(i) == expected

    def test_str_method_appends_multiple_return_cols(self):
        i = InsertQuery("banana", ["pears"], [["lemon"]])
        i.returning("apple, banana 1")
        expected = "INSERT INTO banana"
        expected += "\n(pears)"
        expected += "\nVALUES"
        expected += "\n('lemon')"
        expected += '\nRETURNING apple, "banana 1";'
        assert str(i) == expected

    def test_str_method_appends_return_star(self):
        i = InsertQuery("banana", ["pears"], [["lemon"]])
        i.returning()
        expected = "INSERT INTO banana"
        expected += "\n(pears)"
        expected += "\nVALUES"
        expected += "\n('lemon')"
        expected += '\nRETURNING *;'
        assert str(i) == expected
