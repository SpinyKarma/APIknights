from src.utils.insert import (
    merge,
    diff,
    insert_archetype,
    insert_module
)
from src.utils.formatting import insert_query, update_query
from unittest.mock import Mock, patch, ANY
from copy import deepcopy


class Test_merge:
    def test_returns_empty_dict_when_passed_two_empty_dicts(self):
        assert merge({}, {}) == {}

    def test_returns_full_dict_when_passed_empty_and_full_dict(self):
        assert merge({}, {"banana": 5}) == {"banana": 5}

    def test_returns_combined_dict_when_passed_dicts_no_overlap(self):
        assert merge(
            {"apple": 6},
            {"banana": 5}) == {"apple": 6, "banana": 5}

    def test_returns_combined_dict_when_passed_dicts_overlap_nones(self):
        assert merge(
            {"apple": 6, "banana": None},
            {"banana": 5, "apple": None}
        ) == {"apple": 6, "banana": 5}

    def test_prioritises_2nd_dict_when_overlap(self):
        assert merge(
            {"apple": 6, "banana": 6},
            {"apple": 7}
        ) == {"apple": 7, "banana": 6}

    def test_recursively_merges_when_key_is_dict_for_both(self):
        assert merge(
            {"apple": 6, "banana": 6, "orange": {"colour": 9, "fruit": 8}},
            {"apple": 7, "lemon": 3, "orange": {"fruit": 17}}
        ) == {
            "apple": 7,
            "banana": 6,
            "lemon": 3,
            "orange": {
                "colour": 9,
                "fruit": 17
            }
        }


class Test_diff:
    def test_returns_empty_dict_when_args_are_same(self):
        assert diff({"one": "two"}, {"one": "two"}) == {}

    def test_returns_after_dict_when_no_key_overlap(self):
        assert diff({"one": "two"}, {"three": "four"}) == {"three": "four"}

    def test_returns_differing_keys_when_key_overlap(self):
        assert diff({"one": "two"}, {"one": "five"}) == {"one": "five"}

    def test_ignores_KV_pairs_that_are_same_in_each_dict(self):
        assert diff(
            {"one": "two", "three": "four"},
            {"one": "five", "three": "four"}
        ) == {"one": "five"}


class Test_insert_archetype:
    @patch("src.utils.insert.run")
    def test_runs_insert_query_if_stored_is_empty(self, m_run):
        stored = []
        fresh = {"apple": "orange"}
        query = insert_query("archetypes", fresh, ["archetype_id"])
        insert_archetype(stored, fresh)
        m_run.assert_called_with(query)

    @patch("src.utils.insert.run")
    def test_returns_id_from_query_if_stored_is_empty(self, m_run):
        stored = []
        fresh = {"apple": "orange"}
        m_run.return_value = [{"archetype_id": 15}]
        a_id = insert_archetype(stored, fresh)
        assert a_id == 15

    @patch("src.utils.insert.merge")
    def test_calls_merge_on_both_args_stored_not_empty(self, m_merge):
        stored = [{"archetype_id": 15, "lemon": "pear"}]
        fresh = {"apple": "orange"}
        m_merge.return_value = stored[0]
        insert_archetype(stored, fresh)
        m_merge.assert_called_with(stored[0], fresh, "vb")

    def test_if_merge_equal_to_stored_return_id_from_stored(self):
        stored = [{"archetype_id": 15, "apple": "orange"}]
        fresh = {"apple": "orange"}
        a_id = insert_archetype(stored, fresh)
        assert a_id == 15

    @patch("src.utils.insert.run")
    def test_runs_update_query_if_merged_not_stored(self, m_run):
        stored = [{"archetype_id": 15, "lemon": "pear"}]
        fresh = {"apple": "orange"}
        merged = merge(stored[0], fresh)
        changes = diff(stored[0], merged)
        query = update_query("archetypes", changes, {"archetype_id": 15})
        insert_archetype(stored, fresh)
        m_run.assert_called_with(query)
