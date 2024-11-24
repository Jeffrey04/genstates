"""A library for creating and managing state machines with optional state actions."""

from collections.abc import Callable, Generator, Iterable
from dataclasses import dataclass
from functools import reduce
from types import ModuleType
from typing import Any, Optional, TypeVar, assert_type

import genruler

from genstates.exceptions import (
    DuplicateDestinationError,
    DuplicateTransitionError,
    InvalidInitialStateError,
    MissingDestinationStateError,
    MissingInitialStateError,
    MissingTransitionError,
    NonCallableActionError,
)


@dataclass(frozen=True)
class State[T]:
    """
    A state in a state machine with an optional action.

    Each state has a unique key, a human-readable name, and an optional action that
    can be executed when the state is active.

    Attributes:
        key: Unique identifier for the state
        name: Human-readable name for the state
        action: Optional callable to execute when the state is active
    """
    key: str
    name: str
    action: Callable[..., T] | None

    def do_action(self, *arguments: Any) -> Any:
        """
        Execute this state's action with the given arguments.

        Args:
            *arguments: Arguments to pass to the action

        Returns:
            Result of executing the action
        """
        return self.action(*arguments)


@dataclass(frozen=True)
class Transition:
    """
    A transition between states in a state machine.

    Transitions are directed edges in the state machine graph that connect states.
    Each transition has a rule that determines when it should be taken.

    Attributes:
        key: Unique identifier for the transition
        name: Human-readable name for the transition
        origin: Source state where this transition starts
        destination: Target state where this transition leads
        rule: Function that takes a context dict and returns True if the transition should be taken
    """
    key: str
    name: str
    origin: State
    destination: State
    rule: Callable[[dict[Any, Any]], bool]

    def check_condition(self, context: dict[Any, Any]) -> bool:
        """
        Check if this transition should be taken given the current context.

        Args:
            context: Current state machine context

        Returns:
            True if the transition should be taken, False otherwise
            Returns False if the rule raises an exception
        """
        assert_type(self.rule, Callable[[dict[Any, Any]], bool])
        try:
            return self.rule(context)
        except Exception:
            return False


class Machine:
    """
    A state machine that can transition between states based on rules.

    The machine is configured using a schema that defines states and their transitions.
    Each state can have an optional action that is executed when the state is active.

    Attributes:
        initial: Starting state of the machine
        states: Map of state keys to State objects
        transitions: Map of (state_key, transition_key) pairs to Transition objects
    """
    initial: State
    states: dict[str, State]
    transitions: dict[tuple[str, str], Transition]

    def __init__(
        self, schema: dict[Any, Any], module: ModuleType | None = None
    ) -> None:
        """
        Create a new state machine from a configuration schema.

        Args:
            schema: Configuration dict with states, transitions, and initial state
            module: Optional module containing action functions referenced in the schema

        Raises:
            MissingInitialStateError: No initial state specified
            InvalidInitialStateError: Specified initial state not found
            DuplicateTransitionError: Multiple transitions between same states
            MissingDestinationStateError: Transition to non-existent state
            NonCallableActionError: State action is not callable
        """
        self.states, self.transitions = self._populate(schema["states"], module)

        try:
            initial_state_key = schema["machine"]["initial_state"]
        except KeyError as e:
            raise MissingInitialStateError() from e

        try:
            self.initial = self.states[initial_state_key]
        except KeyError as e:
            raise InvalidInitialStateError(initial_state_key) from e

    def graph(self) -> str:
        """
        Generate a Graphviz DOT representation of the state machine.

        Returns:
            DOT graph notation string for visualization
        """
        nodes = [
            f'    "{state.key}" [label="{state.key}"]' for state in self.states.values()
        ]

        edges = [
            f'    "{transition.origin.key}" -> "{transition.destination.key}" [label="{transition.key}"]'
            for transition in self.transitions.values()
        ]

        return "digraph {\n" + "\n".join(nodes + edges) + "\n}"

    def get_transitions(self, state: State) -> dict[str, Transition]:
        """
        Get all transitions available from a state.

        Args:
            state: Source state

        Returns:
            Map of transition keys to Transition objects
        """
        return {
            key_transition: transition
            for (key_state, key_transition), transition in self.transitions.items()
            if key_state == state.key
        }

    def get_transition(self, state: State, key: str) -> Transition:
        """
        Get a specific transition from a state.

        Args:
            state: Source state
            key: Transition key to find

        Returns:
            The requested transition
        """
        return self.transitions[(state.key, key)]

    def map_action(
        self,
        current_state: State,
        iterable: Iterable[Any],
    ) -> Generator[Any, None, None]:
        """
        Map each item in the iterable through the state machine and execute the resulting state's action.

        Args:
            current_state: Starting state for each item
            iterable: Items to process through the state machine

        Returns:
            Generator of results from executing each state's action
        """
        for item in iterable:
            current_state = self.progress(current_state, item)

            yield current_state.do_action(item)

    def progress(self, state: State, context: dict[Any, Any]) -> State:
        """
        Move to the next state based on the current context.

        Evaluates all transitions from the current state and takes the first valid one.

        Args:
            state: Current state
            context: Context for evaluating transition rules

        Returns:
            Next state after applying transitions

        Raises:
            MissingTransitionError: No valid transitions found
            DuplicateTransitionError: Multiple valid transitions possible
        """
        result = [
            state
            for result, state in (
                (trn.check_condition(context), trn.destination)
                for trn in self.get_transitions(state).values()
            )
            if result is True
        ]

        if len(result) == 0:
            raise MissingTransitionError(state.key, "*")
        if len(result) > 1:
            raise DuplicateTransitionError(state.key, result[0].key)

        return result[0]

    def reduce_action(
        self,
        current_state: State,
        iterable: Iterable[Any],
        initial_value: Any | None = None,
    ) -> Any:
        """
        Reduce an iterable through the state machine using each state's action as the reduction function.

        Args:
            current_state: Starting state for each reduction step
            iterable: Items to process through the state machine
            initial_value: Optional starting value for the reduction

        Returns:
            Final accumulated value after applying all state actions
        """

        def reduce_function(current: Any, incoming: Any) -> Any:
            nonlocal current_state

            current_state = self.progress(current_state, incoming)

            return current_state.do_action(current, incoming)

        if initial_value is None:
            return reduce(reduce_function, iterable)
        else:
            return reduce(reduce_function, iterable, initial_value)

    def _populate(
        self, states: dict[str, Any], module: ModuleType | None
    ) -> tuple[dict[str, State], dict[tuple[str, str], Transition]]:
        """
        Create states and transitions from a configuration dict.

        Args:
            states: Dict with state and transition definitions
            module: Optional module containing action functions

        Returns:
            Tuple of (states_dict, transitions_dict) where:
            - states_dict: Maps state keys to State objects
            - transitions_dict: Maps (state_key, transition_key) to Transition objects

        Raises:
            DuplicateDestinationError: When a state has multiple transitions to the same destination
            MissingDestinationStateError: When a transition references a non-existent destination state
            NonCallableActionError: When a state's action is not callable
            genruler.exceptions.ParseError: When a transition rule has invalid syntax
        """
        result_states, result_transitions = {}, {}

        for state_key, definition in states.items():
            action = None
            if module and definition.get("action"):
                action = getattr(module, definition["action"])
                if not callable(action):
                    raise NonCallableActionError(state_key)

            result_states[state_key] = State(
                key=state_key,
                name=definition.get("name", state_key),
                action=action,
            )

            # Check for duplicate destinations in transitions
            destinations = []
            for trn_key, trn_definition in (
                states[state_key].get("transitions", {}).items()
            ):
                destination = trn_definition["destination"]
                if destination in destinations:
                    raise DuplicateDestinationError(state_key, destination)
                destinations.append(destination)

                result_transitions[(state_key, trn_key)] = {
                    "key": trn_key,
                    "name": trn_definition.get("name", trn_key),
                    "origin": result_states[state_key],
                    "destination": trn_definition["destination"],
                    "rule": genruler.parse(
                        trn_definition.get("rule", "(boolean.tautology)")
                    ),
                }

        try:
            result_transitions = {
                key: Transition(
                    **dict(value, destination=result_states[value["destination"]])
                )
                for key, value in result_transitions.items()
            }
        except KeyError as e:
            raise MissingDestinationStateError(str(e.args[0])) from e

        return result_states, result_transitions
