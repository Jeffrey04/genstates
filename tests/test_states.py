import pytest

from genstates import Machine, State, Transition, Validation
from genstates.exceptions import (
    DuplicateDestinationError,
    DuplicateTransitionError,
    InvalidInitialStateError,
    MissingActionError,
    MissingDestinationStateError,
    MissingInitialStateError,
    MissingTransitionError,
    NonCallableActionError,
    ValidationFailedError,
)


@pytest.fixture
def simple_machine_schema():
    return {
        "machine": {"initial_state": "state1"},
        "states": {
            "state1": {
                "name": "State One",
                "action": None,
                "transitions": {
                    "to_state2": {
                        "name": "Go to State Two",
                        "destination": "state2",
                        "rule": "(boolean.tautology)",
                    }
                },
            },
            "state2": {
                "name": "State Two",
                "action": None,
            },
        },
    }


class TestState:
    def test_creation(self):
        state = State(key="test", name="Test State", action=None)
        assert state.key == "test"
        assert state.name == "Test State"
        assert state.action is None

    def test_action(self):
        def test_action(state, x, y):
            assert isinstance(state, State)
            assert state.key == "test"
            return x + y

        state = State(key="test", name="Test State", action=test_action)
        assert state.action is test_action
        assert state.do_action(1, 2) == 3

        # Test with context
        def test_action_with_context(state, context, x, y):
            assert isinstance(state, State)
            assert state.key == "test"
            assert context["value"] == 42
            return x + y

        state = State(key="test", name="Test State", action=test_action_with_context)
        assert state.do_action(1, 2, context={"value": 42}) == 3

    def test_missing_action(self):
        """Test that executing a state with no action raises MissingActionError."""
        state = State(key="test", name="Test State", action=None)
        with pytest.raises(
            MissingActionError, match="No action defined for state test"
        ):
            state.do_action()


class TestTransition:
    @pytest.fixture
    def states(self):
        return {
            "origin": State(key="start", name="Start State", action=None),
            "destination": State(key="end", name="End State", action=None),
        }

    def test_creation(self, states):
        def always_true(context):
            return True

        transition = Transition(
            key="test_transition",
            name="Test Transition",
            origin=states["origin"],
            destination=states["destination"],
            rule=always_true,
            validation=None,
        )

        assert transition.key == "test_transition"
        assert transition.name == "Test Transition"
        assert transition.origin is states["origin"]
        assert transition.destination is states["destination"]
        assert transition.check_condition({}) is True

    def test_invalid_rule(self, states):
        def invalid_rule(context):
            raise Exception("Invalid rule")

        transition = Transition(
            key="test_transition",
            name="Test Transition",
            origin=states["origin"],
            destination=states["destination"],
            rule=invalid_rule,
            validation=None,
        )

        assert transition.check_condition({}) is False

    def test_validation_pass(self, states):
        """Test that validation passes when rule returns True."""

        def always_true(context):
            return True

        validation = Validation(rule=always_true, message="Should not fail")
        transition = Transition(
            key="test_transition",
            name="Test Transition",
            origin=states["origin"],
            destination=states["destination"],
            rule=always_true,
            validation=validation,
        )

        assert transition.check_condition({}) is True

    def test_validation_fail(self, states):
        """Test that validation failure raises ValidationFailedError."""

        def always_true(context):
            return True

        def always_false(context):
            return False

        validation = Validation(rule=always_false, message="Validation failed")
        transition = Transition(
            key="test_transition",
            name="Test Transition",
            origin=states["origin"],
            destination=states["destination"],
            rule=always_true,
            validation=validation,
        )

        with pytest.raises(
            ValidationFailedError,
            match="Transition test_transition failed validation: Validation failed",
        ):
            transition.check_condition({})

    def test_rule_fail_skips_validation(self, states):
        """Test that validation is skipped when rule returns False."""

        def always_false(context):
            return False

        def validation_error(context):
            raise Exception("Validation should not be called")

        validation = Validation(rule=validation_error, message="Should not be called")
        transition = Transition(
            key="test_transition",
            name="Test Transition",
            origin=states["origin"],
            destination=states["destination"],
            rule=always_false,
            validation=validation,
        )

        assert transition.check_condition({}) is False


class TestMachine:
    def test_initialization(self, simple_machine_schema):
        machine = Machine(simple_machine_schema)
        assert machine.initial.key == "state1"
        assert isinstance(machine.transitions[("state1", "to_state2")].origin, State)
        assert isinstance(
            machine.transitions[("state1", "to_state2")].destination, State
        )
        assert len(machine.states) == 2
        assert len(machine.transitions) == 1

    def test_state_references(self, simple_machine_schema):
        machine = Machine(simple_machine_schema)
        transition = machine.transitions[("state1", "to_state2")]

        # Verify that transitions reference the actual state objects
        assert transition.origin is machine.states["state1"]
        assert transition.destination is machine.states["state2"]

    def test_progress(self, simple_machine_schema):
        machine = Machine(simple_machine_schema)
        next_state = machine.progress(machine.initial, {})
        assert next_state.key == "state2"
        assert next_state is machine.states["state2"]

    def test_progress_no_destination(self):
        schema = {
            "machine": {"initial_state": "state1"},
            "states": {
                "state1": {
                    "name": "State One",
                    "action": None,
                    "transitions": {
                        "to_state2": {
                            "name": "Go to State Two",
                            "destination": "state2",
                            "rule": "(boolean.contradiction)",
                        }
                    },
                },
                "state2": {"name": "State Two", "action": None},
            },
        }
        machine = Machine(schema)
        with pytest.raises(
            MissingTransitionError,
            match="Missing required transition from state1 to \\*",
        ):
            machine.progress(machine.initial, {})

    def test_multiple_valid_transitions(self):
        """
        Test that having multiple valid transitions raises a DuplicateTransitionError.
        """
        schema = {
            "machine": {"initial_state": "state1"},
            "states": {
                "state1": {
                    "name": "State One",
                    "action": None,
                    "transitions": {
                        "to_state2": {
                            "name": "Go to State Two",
                            "destination": "state2",
                            "rule": "(boolean.tautology)",
                        },
                        "to_state3": {
                            "name": "Go to State Three",
                            "destination": "state3",
                            "rule": "(boolean.tautology)",
                        },
                    },
                },
                "state2": {"name": "State Two", "action": None},
                "state3": {"name": "State Three", "action": None},
            },
        }

        machine = Machine(schema)
        with pytest.raises(
            DuplicateTransitionError,
            match="Transition from state1 to state2 already defined",
        ):
            machine.progress(machine.initial, {})

    def test_missing_initial_state(self):
        schema = {"machine": {}, "states": {"state1": {"name": "State One"}}}

        with pytest.raises(MissingInitialStateError):
            Machine(schema)

    def test_invalid_initial_state(self):
        """
        Test that an invalid initial state raises an InvalidInitialStateError.
        """
        schema = {
            "machine": {"initial_state": "nonexistent"},
            "states": {"state1": {"name": "State One"}},
        }

        with pytest.raises(InvalidInitialStateError):
            Machine(schema)

    def test_missing_destination_state(self):
        """
        Test that a missing destination state raises a MissingDestinationStateError.
        """
        schema = {
            "machine": {"initial_state": "state1"},
            "states": {
                "state1": {
                    "name": "State One",
                    "action": None,
                    "transitions": {
                        "to_state2": {
                            "name": "Go to Nonexistent State",
                            "destination": "nonexistent",
                            "rule": "(boolean.tautology)",
                        }
                    },
                },
            },
        }

        with pytest.raises(MissingDestinationStateError):
            Machine(schema)

    def test_multiple_transitions(self):
        schema = {
            "machine": {"initial_state": "state1"},
            "states": {
                "state1": {
                    "name": "State One",
                    "action": None,
                    "transitions": {
                        "to_state2": {
                            "name": "Go to State Two",
                            "destination": "state2",
                            "rule": "(boolean.contradiction)",
                        },
                        "to_state3": {
                            "name": "Go to State Three",
                            "destination": "state3",
                            "rule": "(boolean.tautology)",
                        },
                    },
                },
                "state2": {"name": "State Two", "action": None},
                "state3": {"name": "State Three", "action": None},
            },
        }

        machine = Machine(schema)
        next_state = machine.progress(machine.initial, {})
        assert next_state.key == "state3"
        assert next_state is machine.states["state3"]
        assert len(machine.transitions) == 2

    def test_graph(self, simple_machine_schema):
        machine = Machine(simple_machine_schema)
        dot_graph = machine.graph()

        # Check for node definitions
        assert '"state1" [label="state1"]' in dot_graph
        assert '"state2" [label="state2"]' in dot_graph

        # Check for edge definition
        assert '"state1" -> "state2" [label="to_state2"]' in dot_graph

        # Check overall structure
        assert dot_graph.startswith("digraph {")
        assert dot_graph.endswith("}")

    def test_duplicate_destination(self):
        schema = {
            "machine": {"initial_state": "state1"},
            "states": {
                "state1": {
                    "name": "State One",
                    "action": None,
                    "transitions": {
                        "to_state2_a": {
                            "name": "First transition to State Two",
                            "destination": "state2",
                            "rule": "(boolean.tautology)",
                        },
                        "to_state2_b": {
                            "name": "Second transition to State Two",
                            "destination": "state2",
                            "rule": "(boolean.tautology)",
                        },
                    },
                },
                "state2": {"name": "State Two", "action": None},
            },
        }

        with pytest.raises(DuplicateDestinationError) as exc_info:
            Machine(schema)
        assert exc_info.value.state == "state1"
        assert exc_info.value.destination == "state2"
        assert "State 'state1' has multiple transitions pointing to 'state2'" in str(exc_info.value)

    def test_state_action_from_module(self):
        class TestModule:
            def action1(self, state, x, y):
                assert isinstance(state, State)
                assert state.key == "state1"
                return x + y

            not_callable = 42

        schema = {
            "machine": {"initial_state": "state1"},
            "states": {
                "state1": {
                    "name": "State One",
                    "action": "action1",
                },
            },
        }

        module = TestModule()
        machine = Machine(schema, module)
        assert machine.states["state1"].do_action(1, 2) == 3

    def test_non_callable_action(self):
        class TestModule:
            not_callable = 42

        schema = {
            "machine": {"initial_state": "state1"},
            "states": {
                "state1": {
                    "name": "State One",
                    "action": "not_callable",
                },
            },
        }

        module = TestModule()
        with pytest.raises(
            NonCallableActionError, match="Action for state 'state1' is not callable"
        ):
            Machine(schema, module)

    def test_operator_add_action(self):
        """Test using operator.add as a state action."""
        import operator

        class TestModule:
            def add_wrapper(self, state, x, y):
                """Wrapper around operator.add that ignores state argument."""
                assert isinstance(state, State)
                return operator.add(x, y)

        schema = {
            "machine": {"initial_state": "state1"},
            "states": {
                "state1": {
                    "name": "State One",
                    "action": "add_wrapper",
                },
            },
        }

        module = TestModule()
        machine = Machine(schema, module)

        # Test with integers
        assert machine.states["state1"].do_action(1, 2) == 3

        # Test with context
        assert machine.states["state1"].do_action(1, 2) == 3

        # Test with strings
        assert machine.states["state1"].do_action("hello ", "world") == "hello world"

        # Test with lists
        assert machine.states["state1"].do_action([1, 2], [3, 4]) == [1, 2, 3, 4]

    def test_operator_add_action_with_context(self):
        """Test using operator.add as a state action with required context."""
        import operator

        class TestModule:
            def add_wrapper(self, state, context, x, y):
                """Wrapper around operator.add that requires context."""
                assert isinstance(state, State)
                assert context is not None
                assert context["value"] == 42
                return operator.add(x, y)

        schema = {
            "machine": {"initial_state": "state1"},
            "states": {
                "state1": {
                    "name": "State One",
                    "action": "add_wrapper",
                },
            },
        }

        module = TestModule()
        machine = Machine(schema, module)

        # Test with integers
        assert machine.states["state1"].do_action(1, 2, context={"value": 42}) == 3

        # Test with strings
        assert (
            machine.states["state1"].do_action("hello ", "world", context={"value": 42})
            == "hello world"
        )

        # Test with lists
        assert machine.states["state1"].do_action(
            [1, 2], [3, 4], context={"value": 42}
        ) == [1, 2, 3, 4]

    def test_map_action(self):
        """Test mapping items through state machine with actions."""

        class TestModule:
            def double(self, state, x):
                """Double the input value."""
                assert isinstance(state, State)
                return x * 2

            def triple(self, state, x):
                """Triple the input value."""
                assert isinstance(state, State)
                return x * 3

        schema = {
            "machine": {"initial_state": "start"},
            "states": {
                "start": {
                    "name": "Start State",
                    "action": "double",
                    "transitions": {
                        "to_triple": {
                            "destination": "triple",
                            "rule": "(boolean.tautology)",
                        },
                    },
                },
                "triple": {
                    "name": "Triple State",
                    "action": "triple",
                    "transitions": {
                        "to_triple": {
                            "destination": "triple",
                            "rule": "(boolean.tautology)",
                        },
                    },
                },
            },
        }

        machine = Machine(schema, TestModule())

        items = [4, 8, 12]
        results = list(machine.map_action(machine.initial, items))
        assert results == [12, 24, 36]

    def test_reduce_action(self):
        """Test reducing items through state machine with actions."""
        import operator

        class TestModule:
            def add_wrapper(self, state, x, y):
                """Wrapper around operator.add that ignores state argument."""
                assert isinstance(state, State)
                return operator.add(x, y)

            def mul_wrapper(self, state, x, y):
                """Wrapper around operator.mul that ignores state arguments."""
                return operator.mul(x, y)

        schema = {
            "machine": {"initial_state": "start"},
            "states": {
                "start": {
                    "name": "Start State",
                    "transitions": {
                        "to_multiply": {
                            "name": "Switch to Sum",
                            "destination": "sum",
                            "rule": "(boolean.tautology)",
                        },
                    },
                },
                "sum": {
                    "name": "Sum State",
                    "action": "add_wrapper",
                    "transitions": {
                        "to_multiply": {
                            "name": "Switch to Multiply",
                            "destination": "multiply",
                            "rule": "(boolean.tautology)",
                        },
                    },
                },
                "multiply": {
                    "name": "Multiply State",
                    "action": "mul_wrapper",
                    "transitions": {
                        "to_multiply": {
                            "name": "Switch to Multiply",
                            "destination": "multiply",
                            "rule": "(boolean.tautology)",
                        },
                    },
                },
            },
        }

        machine = Machine(schema, TestModule())

        # Test with initial value
        assert machine.reduce_action(machine.initial, [1, 2, 3], initial_value=0) == 6
        assert machine.reduce_action(machine.initial, [2, 3, 4], initial_value=1) == 36

    def test_foreach_action(self):
        """Test processing items through state machine with foreach_action."""

        class TestModule:
            def __init__(self):
                self.processed = []

            def collect(self, state, x):
                """Store the input value in processed list."""
                assert isinstance(state, State)
                self.processed.append(x)

            def double(self, state, x):
                """Double the input value and store it."""
                assert isinstance(state, State)
                self.processed.append(x * 2)

        schema = {
            "machine": {"initial_state": "start"},
            "states": {
                "start": {
                    "name": "Start State",
                    "action": "collect",
                    "transitions": {
                        "to_double": {
                            "destination": "double",
                            "rule": "(boolean.tautology)",
                        },
                    },
                },
                "double": {
                    "name": "Double State",
                    "action": "double",
                    "transitions": {
                        "to_double": {
                            "destination": "double",
                            "rule": "(boolean.tautology)",
                        },
                    },
                },
            },
        }

        module = TestModule()
        machine = Machine(schema, module)

        # Process items through the state machine
        items = [1, 2, 3]
        machine.foreach_action(machine.initial, items)

        # Items are processed through the state machine:
        # First item: progress from start -> double, then double(1) -> [2]
        # Subsequent items: progress back to double state, double(2) -> [2, 4], double(3) -> [2, 4, 6]
        assert module.processed == [2, 4, 6]

    def test_validation_in_progress(self):
        """Test that validation is checked during state machine progress."""
        schema = {
            "machine": {"initial_state": "state1"},
            "states": {
                "state1": {
                    "name": "State One",
                    "transitions": {
                        "to_state2": {
                            "name": "Go to State Two",
                            "destination": "state2",
                            "rule": "(boolean.tautology)",
                            "validation": {
                                "rule": '(condition.gt (basic.field "value") 0)',
                                "message": "Value must be positive",
                            },
                        }
                    },
                },
                "state2": {"name": "State Two"},
            },
        }

        machine = Machine(schema)

        # Test validation passes
        next_state = machine.progress(machine.initial, {"value": 1})
        assert next_state.key == "state2"

        # Test validation fails
        with pytest.raises(
            ValidationFailedError,
            match="Transition to_state2 failed validation: Value must be positive",
        ):
            machine.progress(machine.initial, {"value": -1})
