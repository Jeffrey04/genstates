# GenStates

GenStates is an implentation of state machine, with [genruler](https://github.com/Jeffrey04/genruler) as the rule engine.

## Usage

```
from genstates import Machine
import yaml

with open('schema.yaml') as file_schema:
    machine = Machine(yaml.safe_load(file_schema))
```

### Fetching states

* Get initial state by `machine.initial`
* Get any state by `machine.states[$key]` where `$key` is the key for the state

### Fetching transitions

* Get all possible transitions for a given `state` by
  ```
  transitions = machine.get_transitions(state)
  ```
* Get a specific transition for a given `state` by
  ```
  transition = machine.get_transition(state, transition_key)
  ```

### Progressing from one state to another

* If you have a known transition, pass in a context dictionary that the rule understands
  ```
  transition.check_condition(context)
  ```
* If you are not sure about the destination, use `.progress()`
  ```
  destination_state = machine.progress(current_state, context)
  ```
  Note that if multiple transitions are possible it will result in an error

## Schema

Assuming you are storing the transition as a YAML

```
machine:
  initial_state: $initial_state

states:
  $state_key: # can have many states
    name: $state_name
    transitions: # can have many transitions
      $transition_key:
        name: $transition_name
        destination: $transition_destination
        rule: $transition_rule
```

where:

* `$initial_state`: a state key value, must be defined in the `states` section
* `$state_key`: a unique key for the state
* `state_name`: a descriptive name for the state
* `$transition_key`:  a unique key for the transition
* `$transition_destination`:  a state key value, must be defined in the states section, pointing back to the same state is allowed
* `$transition_name`:  a descriptive name for the transition
* `$transition_rule`:  a rule that has to return `True`