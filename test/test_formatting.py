from src.utils.formatting import (
    warn,
    err,
    j_d,
    idf,
    lit,
    insert_query,
    update_query
)
from pg8000.native import identifier, literal
from unittest.mock import patch
import json


class Test_warn_err:
    @patch("builtins.print")
    def test_warn_applies_yellow_colour_to_print(self, test_print):
        warn("banana")
        test_print.assert_called_with("\033[93mbanana\033[0m")

    @patch("builtins.print")
    def test_err_applies_red_colour_to_print(self, test_print):
        err("apple")
        test_print.assert_called_with("\033[91mapple\033[0m")


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


class Test_insert_query:
    def test_takes_table_headings_data_uses_idf_on_headings_lit_on_data(self):
        test_table = "banana"
        test_headings = "id 7"
        test_data = "5"
        out = insert_query(test_table, test_headings, test_data)
        expected = """INSERT INTO banana ("id 7") VALUES ('5');"""
        assert out == expected

    def test_takes_multiple_headings_data_as_comma_separated_strings(self):
        test_table = "banana"
        test_headings = "id 7, name"
        test_data = "5, 6"
        out = insert_query(test_table, test_headings, test_data)
        expected = """INSERT INTO banana ("id 7", name) VALUES ('5', '6');"""
        assert out == expected

    def test_insert_ignores_spacing_in_comma_separated_strings(self):
        test_table = "banana"
        test_headings = "id 7,name"
        test_data = "5 , 6"
        out = insert_query(test_table, test_headings, test_data)
        expected = """INSERT INTO banana ("id 7", name) VALUES ('5', '6');"""
        assert out == expected

    def test_takes_multiple_headings_data_as_lists_of_strings(self):
        test_table = "banana"
        test_headings = ["id 7", "name"]
        test_data = ["5", "6"]
        out = insert_query(test_table, test_headings, test_data)
        expected = """INSERT INTO banana ("id 7", name) VALUES ('5', '6');"""
        assert out == expected

    def test_has_returning_option_adds_returning_clause_to_end_of_query(self):
        test_table = "banana"
        test_headings = "id 7"
        test_data = "5"
        test_returns = "id 7"
        out = insert_query(test_table, test_headings, test_data, test_returns)
        expected = """INSERT INTO banana ("id 7") VALUES ('5')"""
        expected += ' RETURNING "id 7";'
        assert out == expected

    def test_star_for_returning_does_not_have_idf_formatting(self):
        test_table = "banana"
        test_headings = "id 7"
        test_data = "5"
        test_returns = "*"
        out = insert_query(test_table, test_headings, test_data, test_returns)
        expected = """INSERT INTO banana ("id 7") VALUES ('5') RETURNING *;"""
        assert out == expected


class Test_update_query:
    def test_takes_table_changes_filters_uses_idf_and_lit_as_needed(self):
        test_table = "banana"
        test_changes = "id 7 = 5"
        test_filters = "id 6 = 3"
        out = update_query(test_table, test_changes, test_filters)
        expected = """UPDATE banana SET "id 7" = '5' WHERE "id 6" = '3';"""
        assert out == expected

    def test_takes_multiple_changes_filters_as_comma_separated_strings(self):
        test_table = "banana"
        test_changes = "id 7 = 5, name = bob"
        test_filters = "id 6 = 3, name = harry"
        out = update_query(test_table, test_changes, test_filters)
        expected = """UPDATE banana SET "id 7" = '5', name = 'bob' WHERE"""
        expected += """ "id 6" = '3' AND name = 'harry';"""
        assert out == expected

    def test_update_ignores_spacing_in_comma_separated_strings(self):
        test_table = "banana"
        test_changes = "id 7=5, name  =bob"
        test_filters = "id 6=  3,   name = harry"
        out = update_query(test_table, test_changes, test_filters)
        expected = """UPDATE banana SET "id 7" = '5', name = 'bob' WHERE"""
        expected += """ "id 6" = '3' AND name = 'harry';"""
        assert out == expected

    def test_takes_multiple_changes_filters_as_lists_of_len2_sublists(self):
        test_table = "banana"
        test_changes = [["id 7", "5"], ["name", "bob"]]
        test_filters = [["id 6", "3"], ["name", "harry"]]
        out = update_query(test_table, test_changes, test_filters)
        expected = """UPDATE banana SET "id 7" = '5', name = 'bob' WHERE"""
        expected += """ "id 6" = '3' AND name = 'harry';"""
        assert out == expected

    def test_takes_multiple_changes_filters_as_dicts(self):
        test_table = "banana"
        test_changes = {"id 7": "5", "name": "bob"}
        test_filters = {"id 6": "3", "name": "harry"}
        out = update_query(test_table, test_changes, test_filters)
        expected = """UPDATE banana SET "id 7" = '5', name = 'bob' WHERE"""
        expected += """ "id 6" = '3' AND name = 'harry';"""
        assert out == expected

    def test_has_returning_option_adds_returning_clause_to_end_of_query(self):
        test_table = "banana"
        test_changes = "id 7 = 5"
        test_filters = "id 6 = 3"
        test_return = "id 7"
        out = update_query(test_table, test_changes, test_filters, test_return)
        expected = """UPDATE banana SET "id 7" = '5' WHERE "id 6" = '3'"""
        expected += """ RETURNING "id 7";"""
        assert out == expected

    def test_star_for_returning_does_not_have_idf_formatting(self):
        test_table = "banana"
        test_changes = "id 7 = 5"
        test_filters = "id 6 = 3"
        test_return = "*"
        out = update_query(test_table, test_changes, test_filters, test_return)
        expected = """UPDATE banana SET "id 7" = '5' WHERE "id 6" = '3'"""
        expected += """ RETURNING *;"""
        assert out == expected
