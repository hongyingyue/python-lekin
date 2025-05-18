# LeKin Scheduling Solver

A flexible and extensible scheduling solver framework for production planning and scheduling problems.

## Features

- Multiple solving strategies:
  - Continuous Time Planning (CTP)
  - Construction Heuristics
  - Meta-heuristics (Genetic Algorithm, Simulated Annealing)
  - Reinforcement Learning
  - Operation Research methods
- Extensible architecture for custom solvers
- Comprehensive constraint handling
- Performance metrics and visualization
- Parallel solving capabilities
- Solution validation and verification

## Installation

```bash
pip install lekin-solver
```

## Quick Start

```python
from lekin.solver import create_solver, solve_scheduling_problem

# Create your problem instance
jobs = [...]
routes = [...]
resources = [...]

# Configure the solver
config = {
    'solver_type': 'ctp',
    'time_window_size': 24,
    'optimization_weights': {
        'makespan': 0.4,
        'resource_utilization': 0.3,
        'tardiness': 0.3
    }
}

# Solve the problem
solution = solve_scheduling_problem(
    jobs=jobs,
    routes=routes,
    resources=resources,
    config=config
)
```

## Architecture

The solver package follows a modular architecture:

```
lekin/solver/
├── core/                 # Core interfaces and base classes
├── strategies/           # Different solving strategies
│   ├── ctp/             # Continuous Time Planning
│   ├── construction/    # Construction heuristics
│   ├── meta/           # Meta-heuristics
│   ├── rl/             # Reinforcement Learning
│   └── or/             # Operation Research
├── constraints/         # Constraint definitions and handlers
├── metrics/            # Performance metrics and evaluation
├── utils/              # Utility functions and helpers
└── visualization/      # Solution visualization tools
```

## Extending the Solver

### Adding a New Solver Strategy

```python
from lekin.solver.core import BaseSolver

class MyCustomSolver(BaseSolver):
    def solve(self, jobs, routes, resources):
        # Implement your solving logic
        pass
```

### Adding New Constraints

```python
from lekin.solver.constraints import BaseConstraint

class MyCustomConstraint(BaseConstraint):
    def check(self, solution):
        # Implement your constraint checking logic
        pass
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 