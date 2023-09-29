from src.utils.debugger import Debug
from unittest.mock import patch, call


class Test_Debug:
    def test_defaults_to_off(self):
        debug = Debug()
        assert debug.enabled == False

    def test_takes_arg_on_init_to_swich_on(self):
        debug = Debug(True)
        assert debug.enabled == True

    def test_on_method_enables_debugger(self):
        debug = Debug()
        debug.on()
        assert debug.enabled == True

    def test_off_method_disables_debugger(self):
        debug = Debug(True)
        debug.off()
        assert debug.enabled == False

    def test_switch_method_toggles_debugger(self):
        debug = Debug()
        debug.switch()
        assert debug.enabled == True
        debug.switch()
        assert debug.enabled == False

    @patch("src.utils.debugger.pprint")
    def test_call_debugger_uses_pprint_if_enabled(self, m_pprint):
        debug = Debug(True)
        debug("banana")
        m_pprint.assert_called_with("banana")

    @patch("src.utils.debugger.pprint")
    def test_call_debugger_does_nothing_if_not_enabled(self, m_pprint):
        debug = Debug()
        debug("banana")
        m_pprint.assert_not_called()

    @patch("src.utils.debugger.pprint")
    def test_multiple_passed_args_passed_to_pprint_in_sequence(self, m_pprint):
        debug = Debug(True)
        debug("banana", "apple", "orange")
        assert m_pprint.call_args_list == [
            call("banana"),
            call("apple"),
            call("orange")
        ]

    @patch("src.utils.debugger.pprint")
    def test_all_kwargs_passed_to_pprint(self, m_pprint):
        debug = Debug(True)
        debug("banana", apple="apple", orange="orange")
        m_pprint.assert_called_with("banana", apple="apple", orange="orange")

    @patch("src.utils.debugger.pprint")
    def test_all_kwargs_passed_to_pprint_for_each_arg(self, m_pprint):
        debug = Debug(True)
        debug("banana", "lemon", apple="apple", orange="orange")
        assert m_pprint.call_args_list == [
            call("banana", apple="apple", orange="orange"),
            call("lemon", apple="apple", orange="orange")
        ]

    @patch("src.utils.debugger.pprint")
    def test_on_takes_same_args_as_call_switches_on_then_calls(self, m_pprint):
        debug = Debug()
        debug.on("banana", "lemon", apple="apple", orange="orange")
        assert m_pprint.call_args_list == [
            call("banana", apple="apple", orange="orange"),
            call("lemon", apple="apple", orange="orange")
        ]

    @patch("src.utils.debugger.pprint")
    def test_warn_adds_yellow_colour_chars_before_pass_to_call(self, m_pprint):
        debug = Debug(True)
        debug.warn("banana")
        m_pprint.assert_called_with("\x1b[93mbanana\x1b[0m")

    @patch("src.utils.debugger.pprint")
    def test_warn_applies_to_each_arg_passed_to_call(self, m_pprint):
        debug = Debug(True)
        debug.warn("banana", "apple")
        assert m_pprint.call_args_list == [
            call("\x1b[93mbanana\x1b[0m"),
            call("\x1b[93mapple\x1b[0m")
        ]

    @patch("src.utils.debugger.pprint")
    def test_warn_passses_kwargs_to_call(self, m_pprint):
        debug = Debug(True)
        debug.warn("banana", "apple", orange="orange")
        assert m_pprint.call_args_list == [
            call("\x1b[93mbanana\x1b[0m", orange="orange"),
            call("\x1b[93mapple\x1b[0m", orange="orange")
        ]

    @patch("src.utils.debugger.pprint")
    def test_err_adds_red_colour_chars_before_pass_to_call(self, m_pprint):
        debug = Debug(True)
        debug.err("banana")
        m_pprint.assert_called_with("\x1b[91mbanana\x1b[0m")

    @patch("src.utils.debugger.pprint")
    def test_err_applies_to_each_arg_passed_to_call(self, m_pprint):
        debug = Debug(True)
        debug.err("banana", "apple")
        assert m_pprint.call_args_list == [
            call("\x1b[91mbanana\x1b[0m"),
            call("\x1b[91mapple\x1b[0m")
        ]

    @patch("src.utils.debugger.pprint")
    def test_err_passses_kwargs_to_call(self, m_pprint):
        debug = Debug(True)
        debug.err("banana", "apple", orange="orange")
        assert m_pprint.call_args_list == [
            call("\x1b[91mbanana\x1b[0m", orange="orange"),
            call("\x1b[91mapple\x1b[0m", orange="orange")
        ]

    @patch("src.utils.debugger.pprint")
    def test_x_func_does_nothing_to_turn_single_statement_off(self, m_pprint):
        debug = Debug(True)
        debug.x()
        m_pprint.assert_not_called()

    def test_x_takes_call_args_to_not_throw_err_when_switched(self):
        debug = Debug(True)
        debug.x("banana", "apple", orange="orange")
        assert True
