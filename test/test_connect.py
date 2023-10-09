from src.utils.connect import connect, run
from unittest.mock import Mock, patch


class Test_connect:
    @patch("src.utils.connect.getenv")
    @patch("src.utils.connect.Connection")
    def test_passes_env_vars_to_connection_object(self, m_Con, m_env):
        m_env.side_effect = ["lemon", "orange", "banana"]
        connect()
        m_Con.assert_called_with(
            "lemon",
            database="orange",
            password="banana"
        )


class Test_run:
    @patch("src.utils.connect.connect")
    def test_queries_db_with_passed_query(self, m_connect):
        m_db = Mock()
        m_db.run.return_value = []
        m_db.columns = []
        m_connect.return_value.__enter__.return_value = m_db
        run("banana")
        m_db.run.assert_called_with("banana")

    @patch("src.utils.connect.connect")
    def test_returns_empty_list_when_db_responds_empty(self, m_connect):
        m_db = Mock()
        m_db.run.return_value = []
        m_db.columns = []
        m_connect.return_value.__enter__.return_value = m_db
        assert run("") == []

    @patch("src.utils.connect.connect")
    def test_returns_empty_list_no_returns_requested_of_db(self, m_connect):
        m_db = Mock()
        m_db.run.return_value = None
        m_db.columns = None
        m_connect.return_value.__enter__.return_value = m_db
        assert run("") == []

    @patch("src.utils.connect.connect")
    def test_one_dict_in_list_when_db_one_row_response(self, m_connect):
        m_db = Mock()
        m_db.run.return_value = [["banana"]]
        m_db.columns = [{"name": "fruit"}]
        m_connect.return_value.__enter__.return_value = m_db
        assert run("") == [{"fruit": "banana"}]

    @patch("src.utils.connect.connect")
    def test_one_dict_per_row_when_db_many_row_response(self, m_connect):
        m_db = Mock()
        m_db.run.return_value = [["banana"], ["lemon"]]
        m_db.columns = [{"name": "fruit"}]
        m_connect.return_value.__enter__.return_value = m_db
        assert run("") == [{"fruit": "banana"}, {"fruit": "lemon"}]

    @patch("src.utils.connect.connect")
    def test_one_key_per_col_when_db_many_col_response(self, m_connect):
        m_db = Mock()
        m_db.run.return_value = [["banana", "yellow"]]
        m_db.columns = [{"name": "fruit"}, {"name": "colour"}]
        m_connect.return_value.__enter__.return_value = m_db
        assert run("") == [{"fruit": "banana", "colour": "yellow"}]

    @patch("src.utils.connect.connect")
    def test_many_col_many_row_res(self, m_connect):
        m_db = Mock()
        m_db.run.return_value = [["banana", "yellow"], ["orange", "orange"]]
        m_db.columns = [{"name": "fruit"}, {"name": "colour"}]
        m_connect.return_value.__enter__.return_value = m_db
        assert run("") == [
            {"fruit": "banana", "colour": "yellow"},
            {"fruit": "orange", "colour": "orange"}
        ]

    @patch("src.utils.connect.connect")
    def test_has_optional_return_type_arg(self, m_con):
        m_db = Mock()
        m_db.run.return_value = [["banana"]]
        m_db.columns = [{"name": "fruit"}]
        m_con.return_value.__enter__.return_value = m_db
        run("", return_type={})
        # asserts that TypeError not raised when extra arg given

    @patch("src.utils.connect.connect")
    def test_does_usual_when_return_type_set_to_empty_dict(self, m_con):
        m_db = Mock()
        m_db.run.return_value = [["banana"]]
        m_db.columns = [{"name": "fruit"}]
        m_con.return_value.__enter__.return_value = m_db
        assert run("", {}) == [{"fruit": "banana"}]

    @patch("src.utils.connect.connect")
    def test_cols_then_rows_in_list_return_type_set_to_empty_list(self, m_con):
        m_db = Mock()
        m_db.run.return_value = [["banana"]]
        m_db.columns = [{"name": "fruit"}]
        m_con.return_value.__enter__.return_value = m_db
        assert run("", []) == [["fruit"], ["banana"]]

    @patch("src.utils.connect.connect")
    def test_list_return_extra_sublists_when_multi_rows(self, m_con):
        m_db = Mock()
        m_db.run.return_value = [["banana"], ["lemon"]]
        m_db.columns = [{"name": "fruit"}]
        m_con.return_value.__enter__.return_value = m_db
        assert run("", []) == [["fruit"], ["banana"], ["lemon"]]

    @patch("src.utils.connect.connect")
    def test_list_return_extends_sublists_when_multi_column(self, m_con):
        m_db = Mock()
        m_db.run.return_value = [["banana", "yellow"]]
        m_db.columns = [{"name": "fruit"}, {"name": "colour"}]
        m_con.return_value.__enter__.return_value = m_db
        assert run("", []) == [["fruit", "colour"], ["banana", "yellow"]]

    @patch("src.utils.connect.connect")
    def test_unallowed_vals_for_return_type_set_to_empty_dict(self, m_con):
        m_db = Mock()
        m_db.run.return_value = [["banana"]]
        m_db.columns = [{"name": "fruit"}]
        m_con.return_value.__enter__.return_value = m_db
        assert run("", "banana") == [{"fruit": "banana"}]
