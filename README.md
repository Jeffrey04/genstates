# Genstates

A flexible state machine library for Python with support for state actions and dynamic transitions.

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Core Concepts](#core-concepts)
   - [State Machine](#state-machine)
   - [States](#states)
   - [Transitions](#transitions)
   - [Actions](#actions)
4. [Configuration](#configuration)
   - [Schema Structure](#schema-structure)
   - [State Configuration](#state-configuration)
   - [Transition Rules](#transition-rules)
5. [Features](#features)
   - [State Actions](#state-actions)
   - [Sequence Processing](#sequence-processing)
     - [Map Action](#map-action)
     - [Reduce Action](#reduce-action)
     - [Foreach Action](#foreach-action)
   - [Visualization](#visualization)
6. [Advanced Usage](#advanced-usage)
   - [Custom Action Modules](#custom-action-modules)
   - [Complex State Transitions](#complex-state-transitions)
7. [Contributing](#contributing)
8. [License](#license)

## Installation

```bash
pip install genstates
```

## Quick Start

You can define your state machine either directly with a Python dictionary or using a YAML file:

### Using Python Dictionary

```python
from genstates import Machine

class Calculator:
    def mul_wrapper(self, state, x, y):
        """Wrapper around multiplication that ignores state argument."""
        return x * y

# Define state machine configuration
schema = {
    "machine": {"initial_state": "start"},
    "states": {
        "start": {
            "name": "Start State",
            "transitions": {
                "to_double": {
                    "destination": "double",
                    "rule": "(boolean.tautology)",
                    "validation": {
                        "rule": '(condition.gt (basic.field "value") 0)',
                        "message": "Number must be positive"
                    }
                }
            }
        },
        "double": {
            "name": "Double State",
            "action": "mul_wrapper",  # Calculator.mul_wrapper
            "transitions": {
                "to_triple": {
                    "destination": "triple",
                    "rule": "(boolean.tautology)",
                    "validation": {
                        "rule": '(condition.gt (basic.field "value") 0)',
                        "message": "Number must be positive"
                    }
                }
            }
        },
        "triple": {
            "name": "Triple State",
            "action": "mul_wrapper",
            "transitions": {
                "to_triple": {
                    "destination": "triple",
                    "rule": "(boolean.tautology)",
                    "validation": {
                        "rule": '(condition.gt (basic.field "value") 0)',
                        "message": "Number must be positive"
                    }
                }
            }
        }
    }
}

# Create state machine with Calculator instance for actions
machine = Machine(schema, Calculator())

# Process sequence of numbers
numbers = [2, 3, 4]
results = list(machine.map_action(machine.initial, numbers))
# [4, 9, 12]  # Each number is processed through the states
```

### Using YAML File

Alternatively, you can define the state machine in a YAML file (`states.yaml`):

```yaml
machine:
  initial_state: start
states:
  start:
    name: Start State
    transitions:
      to_double:
        destination: double
        rule: "(boolean.tautology)"
        validation:
          rule: '(condition.gt (basic.field "value") 0)'
          message: "Number must be positive"
  double:
    name: Double State
    action: mul_wrapper
    transitions:
      to_triple:
        destination: triple
        rule: "(boolean.tautology)"
        validation:
          rule: '(condition.gt (basic.field "value") 0)'
          message: "Number must be positive"
  triple:
    name: Triple State
    action: mul_wrapper
    transitions:
      to_triple:
        destination: triple
        rule: "(boolean.tautology)"
        validation:
          rule: '(condition.gt (basic.field "value") 0)'
          message: "Number must be positive"
```

Then load and use it in Python:

```python
import yaml  # requires pyyaml package
from genstates import Machine

class Calculator:
    def mul_wrapper(self, state, x, y):
        """Wrapper around multiplication that ignores state argument."""
        return x * y

# Load schema from YAML file
with open('states.yaml') as file:
    schema = yaml.safe_load(file)

# Create state machine with Calculator instance for actions
machine = Machine(schema, Calculator())

# Process sequence of numbers
numbers = [2, 3, 4]
results = list(machine.map_action(machine.initial, numbers))
# [4, 9, 12]  # Each number is processed through the states
```

## Core Concepts

### State Machine

The state machine manages a collection of states and their transitions. It:
- Maintains the current state
- Handles state transitions based on rules
- Executes state actions on items
- Provides methods for processing sequences

### States

States represent different stages or conditions in your workflow. Each state can:
- Have an optional action to process items
- Define transitions to other states
- Include metadata like name and description

### Transitions

Transitions define how states can change. Each transition:
- Has a destination state
- Uses a rule to determine when to trigger
- Can include metadata like name and description

### Actions

Actions are functions that process items in a state. They can be:
- Instance methods from a class
- Functions from a Python module
- Any callable that accepts appropriate arguments

## Configuration

### Schema Structure

The state machine is configured using a dictionary with this structure:

```python
schema = {
    "machine": {
        "initial_state": "state_key",  # Key of the initial state
    },
    "states": {
        "state_key": {  # Unique key for this state
            "name": "Human Readable Name",  # Display name for the state
            "action": "action_name",  # Optional: Name of action function
            "transitions": {  # Optional: Dictionary of transitions
                "transition_key": {  # Unique key for this transition
                    "name": "Human Readable Name",  # Display name
                    "destination": "destination_state_key",  # Target state
                    "rule": "(boolean.tautology)",  # Transition rule
                    "validation": {  # Optional: Validation for the transition
                        "rule": "(condition.gt 0)",  # Validation rule
                        "message": "Error message if validation fails"  # Custom error message
                    }
                },
            },
        },
    },
}
```

### State Configuration

States are configured with these fields:
- `name`: Human-readable name for the state
- `action`: Optional name of function to execute
- `transitions`: Dictionary of possible transitions

### Transition Rules

Transitions use [genruler](https://github.com/Jeffrey04/genruler) expressions to determine when they trigger. Common patterns:
- `(boolean.tautology)`: Always transition
- `(condition.equal (basic.field "value") 10)`: Transition when value equals 10
- `(condition.gt (basic.field "count") 5)`: Transition when count greater than 5

## Features

### State Actions

State actions are functions that process items in a state.

#### Action Resolution

1. Actions are specified in state configuration:
   ```python
   "double_state": {
       "name": "Double State",
       "action": "double",  # Name of the function to call
       "transitions": { ... }
   }
   ```

2. Functions are looked up in the provided module:
   ```python
   class NumberProcessor:
       def double(self, state, x, context=None):
           # state is the current State object
           # context is optional and passed from do_action
           return x * 2

   machine = Machine(schema, NumberProcessor())
   ```

#### Action Types

Actions can be defined in several ways. When `do_action` is called with a context parameter, it is passed as the second argument to the action:

1. Instance methods:
   ```python
   class Processor:
       # Without context
       def double(self, state, x):
           # state is the current State object
           return x * 2

       # With context
       def process(self, state, context, x):
           # state is the current State object
           # context is passed from do_action
           return x * context['multiplier']
   ```

2. Module functions (via wrapper class):
   ```python
   class OperatorWrapper:
       # Without context
       def add(self, state, x, y):
           # state is ignored
           return x + y

       # With context
       def add_with_bonus(self, state, context, x, y):
           # state is ignored
           # context is passed from do_action
           return x + y + context['bonus']
   ```

3. Lambda functions:
   ```python
   class Processor:
       # Without context
       double = lambda self, state, x: x * 2

       # With context
       multiply = lambda self, state, context, x: x * context['factor']
   ```

### Sequence Processing

#### Map Action

`map_action(current_state, iterable)` processes items through state transitions and actions.

Key features:
- State transitions occur before processing each item
- Each item is processed by the current state's action
- Results are yielded one at a time

Example:
```python
numbers = [4, 8, 12]
results = list(machine.map_action(machine.initial, numbers))
# Processing flow:
# 4: start -> double -> double(4) = 8
# 8: double -> triple -> triple(8) = 24
# 12: triple -> triple -> triple(12) = 36
```

#### Reduce Action

`reduce_action(current_state, iterable, initial_value=None)` combines items using state actions.

Key features:
- State transitions occur before each reduction
- Current state's action is used as reduction function
- Optional initial value for first reduction

Example:
```python
numbers = [2, 3, 4]
result = machine.reduce_action(machine.initial, numbers, initial_value=1)
# Processing flow:
# (1,2): start -> sum -> add(1,2) = 3
# (3,3): sum -> multiply -> mul(3,3) = 9
# (9,4): multiply -> multiply -> mul(9,4) = 36
```

#### Foreach Action

Process a sequence of items through the state machine, executing each state's action on the items as they flow through:

```python
from genstates import Machine

class Calculator:
    def mul_wrapper(self, state, x, y):
        """Wrapper around multiplication that ignores state argument."""
        return x * y

schema = {
    "machine": {"initial_state": "start"},
    "states": {
        "start": {
            "name": "Start State",
            "action": "mul_wrapper",  # Calculator.mul_wrapper
            "transitions": {
                "to_multiply": {
                    "destination": "multiply",
                    "rule": "(boolean.tautology)",
                }
            }
        },
        "multiply": {
            "name": "Multiply State",
            "action": "mul_wrapper",
            "transitions": {
                "to_multiply": {
                    "destination": "multiply",
                    "rule": "(boolean.tautology)",
                }
            }
        }
    }
}

machine = Machine(schema, Calculator())

# Process numbers through the state machine
numbers = [4, 8, 12]
machine.foreach_action(machine.initial, numbers)
# Each number is first processed by its current state's action,
# then used to determine the next state transition
```

Unlike `map_action` which returns results, `foreach_action` is used when you want to execute state actions for their side effects (e.g., saving to a database, sending notifications) rather than collecting return values.

### Visualization

Export state machine as a Graphviz DOT string:
```python
dot_string = machine.graph()

# Generate visualization using graphviz
import graphviz
graph = graphviz.Source(dot_string)
graph.render("state_machine", format="png")
```

## Advanced Usage

### Custom Action Modules

Create custom modules for complex processing:
```python
class DataProcessor:
    def __init__(self, config):
        self.config = config

    def process(self, data):
        # Complex processing logic
        return processed_data

machine = Machine(schema, DataProcessor(config))
```

### Complex State Transitions

Use transition rules for complex logic:
```python
"transitions": {
    "to_error": {
        "destination": "error",
        "rule": """(boolean.and
            (condition.gt (basic.field "retries") 3)
            (condition.equal (basic.field "status") "failed")
        )""",
    }
}
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.