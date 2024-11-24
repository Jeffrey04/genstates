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
import operator
from genstates import Machine

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
                }
            }
        },
        "double": {
            "name": "Double State",
            "action": "mul",  # operator.mul
            "transitions": {
                "to_triple": {
                    "destination": "triple",
                    "rule": "(boolean.tautology)",
                }
            }
        },
        "triple": {
            "name": "Triple State",
            "action": "mul",
            "transitions": {
                "to_triple": {
                    "destination": "triple",
                    "rule": "(boolean.tautology)",
                }
            }
        }
    }
}

# Create state machine with operator module for actions
machine = Machine(schema, operator)

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
  double:
    name: Double State
    action: mul
    transitions:
      to_triple:
        destination: triple
        rule: "(boolean.tautology)"
  triple:
    name: Triple State
    action: mul
    transitions:
      to_triple:
        destination: triple
        rule: "(boolean.tautology)"
```

Then load and use it in Python:

```python
import operator
import yaml  # requires pyyaml package
from genstates import Machine

# Load schema from YAML file
with open('states.yaml') as file:
    schema = yaml.safe_load(file)

# Create state machine with operator module for actions
machine = Machine(schema, operator)

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
       def double(self, x):
           return x * 2
   
   machine = Machine(schema, NumberProcessor())
   ```

#### Action Types

1. Instance methods:
   ```python
   class Processor:
       def double(self, x):
           return x * 2
   ```

2. Module functions:
   ```python
   import operator
   machine = Machine(schema, operator)  # Use operator.add, mul, etc.
   ```

3. Lambda functions:
   ```python
   class Processor:
       double = lambda self, x: x * 2
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
numbers = [1, 2, 3, 4, 5]
result = machine.reduce_action(machine.initial, numbers, initial_value=0)
# Processing flow:
# (0,1): start -> sum -> add(0,1) = 1
# (1,2): sum -> multiply -> mul(1,2) = 2
# (2,3): multiply -> multiply -> mul(2,3) = 6
# (6,4): multiply -> multiply -> mul(6,4) = 24
# (24,5): multiply -> multiply -> mul(24,5) = 120
```

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