from src.utils.formatting import (
    j_d,
    idf,
    lit,
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

    def test_doesnt_apply_extra_quotes_to_already_validated_str(self):
        test_str = "banana 2"
        valid_str = idf(test_str)
        double_valid_str = idf(valid_str)
        assert double_valid_str == valid_str == '"banana 2"'


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

    def test_doesnt_apply_extra_quotes_to_already_validated_str(self):
        test_str = "banana"
        valid_str = lit(test_str)
        double_valid_str = lit(valid_str)
        assert double_valid_str == valid_str == "'banana'"

    def test_properly_substitutes_quote_not_at_ends_with_two_quotes(self):
        test_str = "banana's"
        test_valid_str = "'banana''s'"
        assert lit(test_str) == test_valid_str
        assert lit(test_valid_str) == test_valid_str
