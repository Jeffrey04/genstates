import logging
from collections.abc import Callable
from dataclasses import dataclass
from functools import reduce
from multiprocessing import Value
from typing import Any, assert_type

import genruler

logger = logging.getLogger(__name__)
logging.basicConfig()


@dataclass(frozen=True)
class State:
    key: str
    name: str


@dataclass(frozen=True)
class Transition:
    key: str
    name: str
    origin: State
    destination: State
    rule: Callable[[dict[Any, Any]], bool]

    def check_condition(self, context: dict[Any, Any]) -> bool:
        assert_type(self.rule, Callable[[dict[Any, Any]], bool])

        return self.rule(context)


class Machine:
    initial: State
    states: dict[str, State]
    transitions: dict[tuple[str, str], Transition]

    def __init__(self, schema: dict[Any, Any]) -> None:
        self.states, self.transitions = self._populate(schema["states"])

        try:
            initial_state_key = schema["machine"]["initial_state"]
        except KeyError as e:
            logger.error("Missing machine initial state configuration")
            raise e

        try:
            self.initial = self.states[initial_state_key]
        except KeyError as e:
            logger.error("Required initial state [%s] is not found", initial_state_key)
            raise e

    def graph(self) -> None:
        """
        Return a graphviz dot graph
        """
        pass

    def get_transitions(self, state: State) -> dict[str, Transition]:
        return {
            key_transition: transition
            for (key_state, key_transition), transition in self.transitions.items()
            if key_state == state.key
        }

    def get_transition(self, state: State, key: str):
        return self.transitions[(state.key, key)]

    def progress(self, state: State, context: dict[Any, Any]) -> State:
        result = [
            state
            for result, state in (
                (trn.rule(context), trn.destination)
                for trn in self.get_transitions(state).values()
            )
            if result is True
        ]

        assert len(result) == 0, "Ensure only 1 destination is possible"

        return result[0]

    def _populate(
        self, states: dict[str, Any]
    ) -> tuple[dict[str, State], dict[tuple[str, str], Transition]]:
        result_states, result_transitions = {}, {}

        for state_key, definition in states.items():
            result_states[state_key] = State(
                key=state_key, name=definition.get("name", state_key)
            )

            for trn_key, trn_definition in (
                states[state_key].get("transitions", {}).items()
            ):
                result_transitions[(state_key, trn_key)] = {
                    "key": trn_key,
                    "name": trn_definition.get("name", trn_key),
                    "origin": states[state_key],
                    "destination": trn_definition["destination"],
                    "rule": genruler.parse(
                        trn_definition.get("rule", "(boolean.tautology)")
                    ),
                }

        try:
            result_transitions = {
                key: Transition(**dict(value, destination=states[value["destination"]]))
                for key, value in result_transitions.items()
            }
        except KeyError as e:
            logger.error("Missing [%s] state definition", e.args[0])
            raise e

        return result_states, result_transitions
