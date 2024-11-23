import pytest

from genstates import Machine, State, Transition


@pytest.fixture
def simple_machine_schema():
    return {
        "machine": {"initial_state": "state1"},
        "states": {
            "state1": {
                "name": "State One",
                "transitions": {
                    "to_state2": {
                        "name": "Go to State Two",
                        "destination": "state2",
                        "rule": "(boolean.tautology)",
                    }
                },
            },
            "state2": {"name": "State Two"},
        },
    }


class TestState:
    def test_creation(self):
        state = State(key="test", name="Test State")
        assert state.key == "test"
        assert state.name == "Test State"


class TestTransition:
    @pytest.fixture
    def states(self):
        return {
            "origin": State(key="start", name="Start State"),
            "destination": State(key="end", name="End State"),
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

    def test_missing_initial_state(self):
        schema = {"machine": {}, "states": {"state1": {"name": "State One"}}}

        with pytest.raises(KeyError):
            Machine(schema)

    def test_invalid_initial_state(self):
        schema = {
            "machine": {"initial_state": "nonexistent"},
            "states": {"state1": {"name": "State One"}},
        }

        with pytest.raises(KeyError):
            Machine(schema)

    def test_missing_destination_state(self):
        schema = {
            "machine": {"initial_state": "state1"},
            "states": {
                "state1": {
                    "name": "State One",
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

        with pytest.raises(KeyError):
            Machine(schema)

    def test_multiple_transitions(self):
        schema = {
            "machine": {"initial_state": "state1"},
            "states": {
                "state1": {
                    "name": "State One",
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
                "state2": {"name": "State Two"},
                "state3": {"name": "State Three"},
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
                "state2": {"name": "State Two"},
            },
        }

        with pytest.raises(ValueError) as exc_info:
            Machine(schema)
        assert "State 'state1' has multiple transitions pointing to 'state2'" in str(exc_info.value)
