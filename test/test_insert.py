from src.utils.insert import (
    merge,
    diff,
    insert_archetype,
    insert_module,
    insert_skill,
    alter_mod,
    add_ids_to_op,
    insert_operator,
    insert_tags,
    insert_operators_tags,
    insert
)
from unittest.mock import patch, call
from copy import deepcopy
from pg8000.exceptions import DatabaseError
import pytest


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
        query = "INSERT INTO archetypes\n(apple)\nVALUES\n('orange')\n"
        query += "RETURNING archetype_id;"
        insert_archetype(stored, fresh)
        m_run.assert_called_with(query)

    @patch("src.utils.insert.run")
    def test_returns_a_id_from_query_if_stored_is_empty(self, m_run):
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
        m_merge.assert_called_with(stored[0], fresh)

    def test_if_merge_equal_to_stored_return_a_id_from_stored(self):
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
        query = "UPDATE archetypes\nSET\napple = 'orange'\n"
        query += "WHERE archetype_id = 15;"
        insert_archetype(stored, fresh)
        m_run.assert_called_with(query)

    def test_does_not_mutate_the_input_arguments(self):
        stored = [{"archetype_id": 15, "apple": "orange"}]
        fresh = {"apple": "orange"}
        stored_clone = deepcopy(stored)
        fresh_clone = deepcopy(fresh)
        insert_archetype(stored, fresh)
        assert stored == stored_clone
        assert fresh == fresh_clone


class Test_insert_skill:
    @patch("src.utils.insert.run")
    def test_runs_insert_query_if_stored_is_empty(self, m_run):
        stored = []
        fresh = {"apple": "orange"}
        query = "INSERT INTO skills\n(apple)\nVALUES\n('orange')\n"
        query += "RETURNING skill_id;"
        insert_skill(stored, fresh)
        m_run.assert_called_with(query)

    @patch("src.utils.insert.run")
    def test_returns_skill_id_from_query_if_stored_is_empty(self, m_run):
        stored = []
        fresh = {"apple": "orange"}
        m_run.return_value = [{"skill_id": 15}]
        s_id = insert_skill(stored, fresh)
        assert s_id == 15

    @patch("src.utils.insert.run")
    def test_does_not_query_db_if_stored_not_empty(self, m_run):
        stored = [{"skill_id": 15}]
        fresh = {"apple": "orange"}
        insert_skill(stored, fresh)
        m_run.assert_not_called()

    def test_returns_skill_id_from_stored_if_stored_not_empty(self):
        stored = [{"skill_id": 15}]
        fresh = {"apple": "orange"}
        s_id = insert_skill(stored, fresh)
        assert s_id == 15

    def test_does_not_mutate_the_input_arguments(self):
        stored = [{"skill_id": 15}]
        fresh = {"apple": "orange"}
        stored_clone = deepcopy(stored)
        fresh_clone = deepcopy(fresh)
        insert_skill(stored, fresh)
        assert stored == stored_clone
        assert fresh == fresh_clone


class Test_insert_module:
    @patch("src.utils.insert.run")
    def test_runs_insert_query_if_stored_is_empty(self, m_run):
        stored = []
        fresh = {"apple": "orange"}
        query = "INSERT INTO modules\n(apple)\nVALUES\n('orange')\n"
        query += "RETURNING module_id;"
        insert_module(stored, fresh)
        m_run.assert_called_with(query)

    @patch("src.utils.insert.run")
    def test_returns_module_id_from_query_if_stored_is_empty(self, m_run):
        stored = []
        fresh = {"apple": "orange"}
        m_run.return_value = [{"module_id": 15}]
        m_id = insert_module(stored, fresh)
        assert m_id == 15

    @patch("src.utils.insert.run")
    def test_does_not_query_db_if_stored_not_empty(self, m_run):
        stored = [{"module_id": 15}]
        fresh = {"apple": "orange"}
        insert_module(stored, fresh)
        m_run.assert_not_called()

    def test_returns_module_id_from_stored_if_stored_not_empty(self):
        stored = [{"module_id": 15}]
        fresh = {"apple": "orange"}
        m_id = insert_module(stored, fresh)
        assert m_id == 15

    def test_does_not_mutate_the_input_arguments(self):
        stored = [{"module_id": 15}]
        fresh = {"apple": "orange"}
        stored_clone = deepcopy(stored)
        fresh_clone = deepcopy(fresh)
        insert_module(stored, fresh)
        assert stored == stored_clone
        assert fresh == fresh_clone


class Test_add_ids_to_op:
    def test_modifies_fresh_using_ids(self):
        a_id = 5
        m_ids = [6, 7]
        s_ids = [8, 9, 10]
        fresh = {"name": "banana"}
        out = add_ids_to_op(fresh, a_id, s_ids, m_ids)
        expected = {
            "name": "banana",
            "archetype_id": 5,
            "module_1_id": 6,
            "module_2_id": 7,
            "skill_1_id": 8,
            "skill_2_id": 9,
            "skill_3_id": 10
        }
        assert out == expected

    def test_allows_for_fewer_than_2_modules(self):
        a_id = 5
        m_ids = [6]
        s_ids = [8, 9, 10]
        fresh = {"name": "banana"}
        out = add_ids_to_op(fresh, a_id, s_ids, m_ids)
        expected = {
            "name": "banana",
            "archetype_id": 5,
            "module_1_id": 6,
            "skill_1_id": 8,
            "skill_2_id": 9,
            "skill_3_id": 10
        }
        assert out == expected

    def test_allows_for_fewer_than_3_skills(self):
        a_id = 5
        m_ids = [6]
        s_ids = [8]
        fresh = {"name": "banana"}
        out = add_ids_to_op(fresh, a_id, s_ids, m_ids)
        expected = {
            "name": "banana",
            "archetype_id": 5,
            "module_1_id": 6,
            "skill_1_id": 8
        }
        assert out == expected

    def test_alter_info_from_fresh_to_none(self):
        a_id = 5
        m_ids = [6]
        s_ids = [8]
        fresh = {"name": "banana", "alter": "orange"}
        out = add_ids_to_op(fresh, a_id, s_ids, m_ids)
        expected = {
            "name": "banana",
            "archetype_id": 5,
            "module_1_id": 6,
            "skill_1_id": 8,
            "alter": None
        }
        assert out == expected

    def test_does_not_mutate_the_input_args(self):
        a_id = 5
        m_ids = [6]
        s_ids = [8]
        fresh = {"name": "banana", "alter": "orange"}
        m_ids_clone = [6]
        s_ids_clone = [8]
        fresh_clone = {"name": "banana", "alter": "orange"}
        add_ids_to_op(fresh, a_id, s_ids, m_ids)
        assert m_ids == m_ids_clone
        assert s_ids == s_ids_clone
        assert fresh == fresh_clone


class Test_insert_operator:
    @patch("src.utils.insert.run")
    def test_runs_insert_query_if_stored_is_empty(self, m_run):
        stored = []
        id_fresh = {"apple": "orange"}
        query = "INSERT INTO operators\n(apple)\nVALUES\n('orange')\n"
        query += "RETURNING operator_id;"
        insert_operator(stored, id_fresh)
        m_run.assert_called_with(query)

    @patch("src.utils.insert.run")
    def test_returns_op_id_from_query_if_stored_is_empty(self, m_run):
        stored = []
        id_fresh = {"apple": "orange"}
        m_run.return_value = [{"operator_id": 15}]
        o_id = insert_operator(stored, id_fresh)
        assert o_id == 15

    @patch("src.utils.insert.run")
    def test_does_not_query_db_if_stored_not_empty(self, m_run):
        stored = [{"operator_id": 15}]
        id_fresh = {"apple": "orange"}
        insert_operator(stored, id_fresh)
        m_run.assert_not_called()

    def test_returns_op_id_from_stored_if_stored_not_empty(self):
        stored = [{"operator_id": 15}]
        id_fresh = {"apple": "orange"}
        o_id = insert_operator(stored, id_fresh)
        assert o_id == 15

    def test_does_not_mutate_the_input_arguments(self):
        stored = [{"operator_id": 15}]
        id_fresh = {"apple": "orange"}
        stored_clone = deepcopy(stored)
        id_fresh_clone = deepcopy(id_fresh)
        insert_operator(stored, id_fresh)
        assert stored == stored_clone
        assert id_fresh == id_fresh_clone


class Test_alter_mod:
    @patch("src.utils.insert.run")
    def test_if_alter_name_is_None_do_nothing(self, m_run):
        alter_mod(None, 1)
        m_run.assert_not_called()

    @patch("src.utils.insert.run")
    def test_if_alter_not_None_query_db_for_alters_op_id(self, m_run):
        query = "SELECT operator_id FROM operators\n"
        query += "WHERE operator_name = 'orange';"
        alter_mod("orange", 1)
        assert call(query) in m_run.call_args_list

    @patch("src.utils.insert.run")
    def test_if_alter_not_in_db_then_do_nothing_more(self, m_run):
        m_run.return_value = []
        alter_mod("orange", 1)
        m_run.assert_called_once()

    @patch("src.utils.insert.run")
    def test_if_alter_in_db_update_op_and_alter_alter_id(self, m_run):
        m_run.return_value = [{"operator_id": 5}]
        op_query = "UPDATE operators\nSET\nalter = 5\nWHERE operator_id = 1;"
        alt_query = "UPDATE operators\nSET\nalter = 1\nWHERE operator_id = 5;"
        alter_mod("orange", 1)
        assert call(op_query) == m_run.call_args_list[1]
        assert call(alt_query) == m_run.call_args_list[2]


class Test_insert_tags:
    @patch("src.utils.insert.run")
    def test_does_not_query_db_if_no_new_tags(self, m_run):
        stored = {"banana": 1}
        fresh = ["banana"]
        insert_tags(stored, fresh)
        m_run.assert_not_called()

    def test_return_tag_ids_for_tags_in_fresh_if_all_in_stored(self):
        stored = {"banana": 1}
        fresh = ["banana"]
        tag_ids = insert_tags(stored, fresh)
        assert tag_ids == [1]

    @patch("src.utils.insert.run")
    def test_makes_insert_query_for_each_new_tag(self, m_run):
        stored = {"banana": 1}
        fresh = ["lemon", "apple", "banana"]
        query_1 = "INSERT INTO tags\n(tag_name)\nVALUES\n('lemon')\n"
        query_1 += "RETURNING tag_id;"
        query_2 = "INSERT INTO tags\n(tag_name)\nVALUES\n('apple')\n"
        query_2 += "RETURNING tag_id;"
        insert_tags(stored, fresh)
        assert m_run.call_args_list == [call(query_1), call(query_2)]

    @patch("src.utils.insert.run")
    def test_appends_returned_tag_id_for_each_new_tag(self, m_run):
        stored = {"banana": 1}
        fresh = ["lemon", "apple"]
        m_run.side_effect = [[{"tag_id": 7}], [{"tag_id": 5}]]
        tag_ids = insert_tags(stored, fresh)
        assert tag_ids == [7, 5]

    @patch("src.utils.insert.run")
    def test_compiles_both_tag_sources_into_returned_list(self, m_run):
        stored = {"banana": 1}
        fresh = ["lemon", "apple", "banana", "lime"]
        m_run.side_effect = [[{"tag_id": 7}], [{"tag_id": 5}], [{"tag_id": 3}]]
        tag_ids = insert_tags(stored, fresh)
        assert tag_ids == [7, 5, 1, 3]


class Test_insert_operators_tags:
    @patch("src.utils.insert.run")
    def test_does_nothing_if_all_tag_ids_in_stored(self, m_run):
        stored_tag_ids = [1, 2, 3]
        op_id = 16
        tag_ids = [2, 3]
        insert_operators_tags(stored_tag_ids, op_id, tag_ids)
        m_run.assert_not_called()

    @patch("src.utils.insert.run")
    def test_makes_insert_query_for_each_new_tag(self, m_run):
        stored_tag_ids = [1, 2, 3]
        op_id = 16
        tag_ids = [1, 2, 3, 4, 5]
        query_1 = "INSERT INTO operators_tags\n(tag_id, operator_id)\n"
        query_1 += "VALUES\n(4, 16);"
        query_2 = "INSERT INTO operators_tags\n(tag_id, operator_id)\n"
        query_2 += "VALUES\n(5, 16);"
        insert_operators_tags(stored_tag_ids, op_id, tag_ids)
        assert m_run.call_args_list == [call(query_1), call(query_2)]


class Test_insert:
    o_data = {"operator_name": "banana"}
    a_data = {"archetype_name": "apple"}
    s_data = [
        {"skill_name": "orange_1"},
        {"skill_name": "orange_2"},
        {"skill_name": "orange_3"}
    ]
    m_data = [
        {"module_name": "lemon_1"},
        {"module_name": "lemon_2"}
    ]
    t_data = ["pear", "pineapple"]
    run_list = ["stored_a", "stored_s_1"]

    @patch("src.utils.insert.connect")
    @patch("src.utils.insert.log.warn")
    def test_gives_warning_message_if_db_doesnt_exist(self, m_warn, m_connect):
        m_connect.side_effect = DatabaseError
        with pytest.raises(DatabaseError):
            insert(1, 2, 3, 4, 5)
        m_warn.assert_called_with(
            "Database doesn't exist yet, run 'reset-db.sh' to initialise"
        )
