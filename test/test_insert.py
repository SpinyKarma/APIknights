from src.utils.insert import (
    merge,
    insert_archetype
)
from src.utils.formatting import select_query, insert_query, update_query
from src.utils.connect import run
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


class Test_insert_archetype:
    fake = {"archetype_name": "banana"}
    headings = list(fake.keys())
    data = list(fake.values())

    @patch("src.utils.insert.connect")
    @patch("src.utils.insert.run")
    def test_does_not_mutate_passed_dict(self, mock_run, mock_connect):
        fake_clone = deepcopy(self.fake)
        mock_run.side_effect = [
            [{"archetype_id": 17, "archetype_name": "banana"}]
        ]
        insert_archetype(self.fake)
        assert fake_clone == self.fake

    @patch("src.utils.insert.connect")
    @patch("src.utils.insert.run")
    # connect patched to stop test's attempts to connect, not neded for testing
    def test_queries_db_using_archetype_name_of_arg(
        self, mock_run, mock_connect
    ):
        mock_run.side_effect = [
            [{"archetype_id": 1, "archetype_name": "banana"}]
        ]
        insert_archetype(self.fake)
        cond = {"archetype_name": self.fake["archetype_name"]}
        query = select_query("archetypes", "*", cond)
        mock_run.assert_called_with(ANY, query)

    @patch("src.utils.insert.connect")
    @patch("src.utils.insert.run")
    def test_returns_archetype_id_of_res_if_not_empty(
        self, mock_run, mock_connect
    ):
        mock_run.side_effect = [
            [{"archetype_id": 17, "archetype_name": "banana"}]
        ]
        id = insert_archetype(self.fake)
        assert id == 17

    @patch("src.utils.insert.connect")
    @patch("src.utils.insert.run")
    def test_runs_insert_query_with_passed_info_if_res_empty(
        self, mock_run, mock_connect
    ):
        mock_run.side_effect = [[], [{"archetype_id": 95}]]
        id = insert_archetype(self.fake)
        query = insert_query(
            "archetypes", self.headings, self.data, "archetype_id"
        )
        mock_run.assert_called_with(ANY, query)
        assert id == 95

    @patch("src.utils.insert.connect")
    @patch("src.utils.insert.run")
    def test_runs_update_query_if_needed_res_not_empty(
        self, mock_run, mock_connect
    ):
        mock_run.side_effect = [[{"archetype_id": 17}], []]
        insert_archetype(self.fake)
        query = update_query(
            "archetypes", {"archetype_name": "banana"}, {"archetype_id": 17}
        )
        mock_run.assert_called_with(ANY, query)
