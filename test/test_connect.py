from src.utils.connect import connect, run
from unittest.mock import Mock, patch


class Test_connect:
    @patch("src.utils.connect.getenv")
    @patch("src.utils.connect.Connection")
    def test_passes_env_vars_to_connection_object(self, mock_Con, mock_env):
        mock_env.side_effect = ["lemon", "orange", "banana"]
        connect()
        mock_Con.assert_called_with(
            "lemon",
            database="orange",
            password="banana"
        )


class Test_run:
    @patch("src.utils.connect.connect")
    def test_queries_db_with_passed_query(self, mock_connect):
        mock_db = Mock()
        mock_db.run.return_value = []
        mock_db.columns = []
        mock_connect.return_value.__enter__.return_value = mock_db
        run("banana")
        mock_db.run.assert_called_with("banana")

    @patch("src.utils.connect.connect")
    def test_returns_empty_list_when_db_responds_empty(self, mock_connect):
        mock_db = Mock()
        mock_db.run.return_value = []
        mock_db.columns = []
        mock_connect.return_value.__enter__.return_value = mock_db
        assert run("") == []

    @patch("src.utils.connect.connect")
    def test_one_dict_in_list_when_db_one_row_response(self, mock_connect):
        mock_db = Mock()
        mock_db.run.return_value = [["banana"]]
        mock_db.columns = [{"name": "fruit"}]
        mock_connect.return_value.__enter__.return_value = mock_db
        assert run("") == [{"fruit": "banana"}]

    @patch("src.utils.connect.connect")
    def test_one_dict_per_row_when_db_many_row_response(self, mock_connect):
        mock_db = Mock()
        mock_db.run.return_value = [["banana"], ["lemon"]]
        mock_db.columns = [{"name": "fruit"}]
        mock_connect.return_value.__enter__.return_value = mock_db
        assert run("") == [{"fruit": "banana"}, {"fruit": "lemon"}]

    @patch("src.utils.connect.connect")
    def test_one_key_per_col_when_db_many_col_response(self, mock_connect):
        mock_db = Mock()
        mock_db.run.return_value = [["banana", "yellow"]]
        mock_db.columns = [{"name": "fruit"}, {"name": "colour"}]
        mock_connect.return_value.__enter__.return_value = mock_db
        assert run("") == [{"fruit": "banana", "colour": "yellow"}]

    @patch("src.utils.connect.connect")
    def test_many_col_many_row_res(self, mock_connect):
        mock_db = Mock()
        mock_db.run.return_value = [["banana", "yellow"], ["orange", "orange"]]
        mock_db.columns = [{"name": "fruit"}, {"name": "colour"}]
        mock_connect.return_value.__enter__.return_value = mock_db
        assert run("") == [
            {"fruit": "banana", "colour": "yellow"},
            {"fruit": "orange", "colour": "orange"}
        ]
