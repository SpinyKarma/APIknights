from src.utils.insert import (
    dict_res,
    merge,
)
from unittest.mock import Mock


class Test_dict_res:
    def test_uses_db_to_run_query(self):
        mock_db = Mock()
        mock_db.run = Mock(return_value=[])
        mock_db.columns = []
        test_query = "banana"
        dict_res(mock_db, test_query)
        mock_db.run.assert_called_with(test_query)

    def test_packages_rows_and_columns_from_response_into_dicts(self):
        mock_db = Mock()
        mock_db.run = Mock(return_value=[
            ["banana", "yellow"],
            ["orange", "orange"]
        ])
        mock_db.columns = [
            {"name": "fruit"},
            {"name": "colour"}
        ]
        test_query = "banana"
        out = dict_res(mock_db, test_query)
        assert out == [
            {"fruit": "banana", "colour": "yellow"},
            {"fruit": "orange", "colour": "orange"}
        ]


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
