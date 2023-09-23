from src.utils.formatting import (
    j_d,
    idf,
    lit,
    select_query,
    insert_query,
    update_query,
    MismatchKeysErr
)
import pytest
from pg8000.native import identifier, literal
from unittest.mock import patch
import json


class Test_j_d:
    def test_j_d_converts_dicts_to_valid_json_format(self):
        test_dict = {"apple": "banana"}
        test_json = json.dumps(test_dict)
        out = j_d(test_dict)
        assert isinstance(out, str)
        assert j_d(test_dict) == test_json

    def test_j_d_ignores_non_dicts(self):
        test_str = "apple"
        test_int = 15
        test_list = [1, 2, "three", 4.5]
        assert j_d(test_str) == test_str
        assert j_d(test_int) == test_int
        assert j_d(test_list) == test_list


class Test_idf:
    def test_idf_applies_identifier_to_single_string(self):
        test_str = "apple banana"
        id = identifier(test_str)
        out = idf(test_str)
        assert id == out

    def test_idf_applies_identifier_to_each_item_in_list(self):
        test_list = ["one", "two", "3", "for five"]
        out = idf(test_list)
        for i in range(len(test_list)):
            assert identifier(test_list[i]) == out[i]

    def test_idf_applies_identifier_recursively_to_each_item_sublists(self):
        test_list = [["one", "two", "3"], ["for", "five", "sick 7"]]
        flat_list = [item for sublist in test_list for item in sublist]
        out = idf(test_list)
        flat_out = [item for sublist in out for item in sublist]
        for i in range(len(flat_list)):
            assert identifier(flat_list[i]) == flat_out[i]

    def test_idf_does_not_modify_when_handling_star(self):
        test_str = "*"
        assert idf(test_str) == test_str


class Test_lit:
    def test_lit_applies_literal_to_single_string(self):
        test_str = "apple"
        id = literal(test_str)
        out = lit(test_str)
        assert id == out

    def test_lit_applies_literal_to_each_item_in_list(self):
        test_list = ["one", 2, "3", "for"]
        out = lit(test_list)
        for i in range(len(test_list)):
            assert literal(test_list[i]) == out[i]

    def test_lit_applies_literal_and_j_d_to_each_item_in_list(self):
        test_list = ["one", 2, "3", "for", {5: "sick"}]
        out = lit(test_list)
        for i in range(len(test_list)):
            assert literal(j_d(test_list[i])) == out[i]

    def test_lit_applies_literal_j_d_recursively_to_each_item_sublists(self):
        test_list = [["one", "two", "3"], ["for", "five", {"sick": 7}]]
        flat_list = [item for sublist in test_list for item in sublist]
        out = lit(test_list)
        flat_out = [item for sublist in out for item in sublist]
        for i in range(len(flat_list)):
            assert literal(j_d(flat_list[i])) == flat_out[i]


class Test_select_query:
    def test_returns_select_all_when_only_passed_table(self):
        query = select_query("banana")
        assert query == "SELECT * FROM banana;"

    def test_applies_idf_to_table_name(self):
        query = select_query("banana 1")
        assert query == 'SELECT * FROM "banana 1";'

    def test_parses_list_of_columns_to_select(self):
        query = select_query("banana", ["apple"])
        assert query == "SELECT apple FROM banana;"

    def test_correctly_separates_multiple_column_entries(self):
        query = select_query("banana", ["apple", "orange"])
        assert query == "SELECT apple, orange FROM banana;"

    def test_applies_idf_to_each_column_heading(self):
        query = select_query("banana", ["apple 2", "orange 3"])
        assert query == 'SELECT "apple 2", "orange 3" FROM banana;'

    def test_one_col_can_be_passed_as_str(self):
        query = select_query("banana", "apple 2")
        assert query == 'SELECT "apple 2" FROM banana;'

    def test_multiple_cols_can_be_passed_as_comma_separated_string(self):
        query = select_query("banana", "apple 2, orange 3")
        assert query == 'SELECT "apple 2", "orange 3" FROM banana;'

    def test_parses_dict_of_filters_to_apply(self):
        query = select_query("banana", "*", {"lemon": "lime"})
        assert query == "SELECT * FROM banana WHERE lemon = 'lime';"

    def test_correctly_separates_multiple_filters(self):
        query = select_query(
            "banana", "*", {"lemon": "lime", "pear": "coconut"})
        expected = "SELECT * FROM banana WHERE lemon = 'lime'"
        expected += " AND pear = 'coconut';"
        assert query == expected

    def test_applies_idf_and_lit_to_each_filter_pair(self):
        query = select_query("banana", "*", {"apple 2": "orange 3"})
        expected = 'SELECT * FROM banana WHERE "apple 2" '
        expected += "= 'orange 3';"
        assert query == expected


class Test_insert_query:
    def test_applies_lit_to_row_data(self):
        query = insert_query("banana", [{"lemon": "lime"}])
        expected = "INSERT INTO banana (lemon) VALUES ('lime');"
        assert query == expected

    def test_applies_idf_to_table_name(self):
        query = insert_query("banana 1", [{"lemon": "lime"}])
        expected = '''INSERT INTO "banana 1" (lemon) VALUES ('lime');'''
        assert query == expected

    def test_applies_idf_to_col_names(self):
        query = insert_query("banana", [{"lemon 2": "lime"}])
        expected = '''INSERT INTO banana ("lemon 2") VALUES ('lime');'''
        assert query == expected

    def test_can_pass_data_as_dict_when_only_one_row(self):
        query = insert_query("banana", {"lemon": "lime"})
        expected = "INSERT INTO banana (lemon) VALUES ('lime');"
        assert query == expected

    def test_can_pass_multiple_rows_one_per_dict(self):
        query = insert_query("banana", [
            {"lemon": "lime"},
            {"lemon": "orange"},
            {"lemon": "grapefruit"}
        ])
        expected = "INSERT INTO banana (lemon) VALUES ('lime'), "
        expected += "('orange'), ('grapefruit');"
        assert query == expected

    def test_can_pass_multiple_columns_one_per_key(self):
        query = insert_query("banana", {"lemon": "lime", "apple": "pear"})
        expected = "INSERT INTO banana (lemon, apple) VALUES ('lime', 'pear');"
        assert query == expected

    def test_raises_mismatch_error_when_keys_are_not_same_in_each_dict(self):
        with pytest.raises(MismatchKeysErr):
            insert_query("banana", [{"one": "two"}, {"three": "four"}])

    def test_optionally_takes_return_column_names(self):
        query = insert_query("banana", [{"lemon": "lime"}], ["apple"])
        expected = "INSERT INTO banana (lemon) VALUES ('lime')"
        expected += " RETURNING apple;"
        assert query == expected

    def test_applies_idf_to_return_column_names(self):
        query = insert_query("banana", [{"lemon": "lime"}], ["apple 1"])
        expected = "INSERT INTO banana (lemon) VALUES ('lime')"
        expected += ' RETURNING "apple 1";'
        assert query == expected

    def test_one_return_can_be_passed_as_str(self):
        query = insert_query("banana", [{"lemon": "lime"}], "apple 1")
        expected = "INSERT INTO banana (lemon) VALUES ('lime')"
        expected += ' RETURNING "apple 1";'
        assert query == expected

    def test_multiple_returns_can_be_passed_as_comma_separated_string(self):
        query = insert_query(
            "banana",
            [{"lemon": "lime"}],
            "apple 1, peach 2")
        expected = "INSERT INTO banana (lemon) VALUES ('lime')"
        expected += ' RETURNING "apple 1", "peach 2";'
        assert query == expected


class Test_update_query:
    def test_applies_lit_to_row_data(self):
        query = update_query("banana", {"lemon": "lime"})
        expected = "UPDATE banana SET lemon = 'lime';"
        assert query == expected

    def test_applies_idf_to_table_name(self):
        query = update_query("banana 1", {"lemon": "lime"})
        expected = """UPDATE "banana 1" SET lemon = 'lime';"""
        assert query == expected

    def test_applies_idf_to_col_names(self):
        query = update_query("banana", {"lemon 1": "lime"})
        expected = """UPDATE banana SET "lemon 1" = 'lime';"""
        assert query == expected

    def test_parses_multiple_changes(self):
        query = update_query("banana", {"lemon": "lime", "apple": "pear"})
        expected = "UPDATE banana SET lemon = 'lime', apple = 'pear';"
        assert query == expected

    def test_takes_filters_dict_to_control_scope_of_update(self):
        query = update_query("banana", {"lemon": "lime"}, {"apple": "pear"})
        expected = "UPDATE banana SET lemon = 'lime' WHERE apple = 'pear';"
        assert query == expected

    def test_correctly_separates_multiple_filters(self):
        query = update_query(
            "banana",
            {"lemon": "lime"},
            {"apple": "pear", "pineapple": "coconut"}
        )
        expected = "UPDATE banana SET lemon = 'lime' WHERE apple = 'pear' "
        expected += "AND pineapple = 'coconut';"
        assert query == expected

    def test_applies_idf_to_filters_col_headings(self):
        query = update_query("banana", {"lemon": "lime"}, {"apple 1": "pear"})
        expected = "UPDATE banana SET lemon = 'lime' WHERE "
        expected += """"apple 1" = 'pear';"""
        assert query == expected

    def test_optionally_takes_return_column_names(self):
        query = update_query(
            "banana",
            {"lemon": "lime"},
            {"apple": "pear"},
            ["peach"])
        expected = "UPDATE banana SET lemon = 'lime' WHERE apple = 'pear'"
        expected += " RETURNING peach;"
        assert query == expected

    def test_applies_idf_to_return_column_names(self):
        query = update_query(
            "banana",
            {"lemon": "lime"},
            {"apple": "pear"},
            ["peach 1"])
        expected = "UPDATE banana SET lemon = 'lime' WHERE apple = 'pear'"
        expected += ' RETURNING "peach 1";'
        assert query == expected

    def test_one_return_can_be_passed_as_str(self):
        query = update_query(
            "banana",
            {"lemon": "lime"},
            {"apple": "pear"},
            "peach 1")
        expected = "UPDATE banana SET lemon = 'lime' WHERE apple = 'pear'"
        expected += ' RETURNING "peach 1";'
        assert query == expected

    def test_multiple_returns_can_be_passed_as_comma_separated_string(self):
        query = update_query(
            "banana",
            {"lemon": "lime"},
            {"apple": "pear"},
            "peach 1, pineapple 2")
        expected = "UPDATE banana SET lemon = 'lime' WHERE apple = 'pear'"
        expected += ' RETURNING "peach 1", "pineapple 2";'
        assert query == expected
