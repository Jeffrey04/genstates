"""Exceptions for the genstates library."""


class GenStatesException(Exception):
    """Base exception for all genstates exceptions."""

    pass


class DuplicateTransitionError(GenStatesException):
    """Raised when a transition is defined more than once."""

    def __init__(self, from_state: str, to_state: str):
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(f"Transition from {from_state} to {to_state} already defined")


class MissingTransitionError(GenStatesException):
    """Raised when a required transition is missing."""

    def __init__(self, from_state: str, to_state: str):
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(f"Missing required transition from {from_state} to {to_state}")


class MissingInitialStateError(GenStatesException):
    """Raised when initial state is not defined in the state machine."""

    def __init__(self):
        super().__init__("Initial state must be defined in state machine configuration")


class InvalidInitialStateError(GenStatesException):
    """Raised when the specified initial state is not found in the state machine."""

    def __init__(self, state: str):
        self.state = state
        super().__init__(f"Initial state '{state}' is not defined in state machine")


class MissingDestinationStateError(GenStatesException):
    """Raised when a transition's destination state is not found in the state machine."""

    def __init__(self, destination: str):
        self.destination = destination
        super().__init__(f"Destination state '{destination}' is not defined in state machine")


class NonCallableActionError(GenStatesException):
    """Raised when a state's action is not callable."""

    def __init__(self, state: str):
        self.state = state
        super().__init__(f"Action for state '{state}' is not callable")


class DuplicateDestinationError(GenStatesException):
    """Raised when a state has multiple transitions to the same destination."""

    def __init__(self, state: str, destination: str):
        self.state = state
        self.destination = destination
        super().__init__(
            f"State '{state}' has multiple transitions pointing to '{destination}'"
        )
