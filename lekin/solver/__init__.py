"""
LeKin Scheduling Solver

This module provides a flexible and extensible framework for solving scheduling problems.
It supports various solving strategies including:
- Continuous Time Planning (CTP)
- Construction Heuristics
- Meta-heuristics
- Reinforcement Learning
- Operation Research methods
"""

from typing import Any, Dict, List, Optional

from lekin.lekin_struct.job import Job
from lekin.lekin_struct.resource import Resource
from lekin.lekin_struct.route import Route
from lekin.solver.core.base_solver import BaseSolver
from lekin.solver.core.ctp_solver import CTPSolver


def create_solver(solver_type: str, config: Optional[Dict[str, Any]] = None) -> BaseSolver:
    """Create a solver instance of the specified type.

    Args:
        solver_type: Type of solver to create ('ctp', 'construction', 'meta', 'rl', 'or')
        config: Optional configuration dictionary

    Returns:
        A solver instance

    Raises:
        ValueError: If solver_type is not supported
    """
    solvers = {
        "ctp": CTPSolver,
        # Add other solver types here as they are implemented
    }

    if solver_type not in solvers:
        raise ValueError(f"Unsupported solver type: {solver_type}")

    return solvers[solver_type](config)


def solve_scheduling_problem(
    jobs: List[Job],
    routes: List[Route],
    resources: List[Resource],
    solver_type: str = "ctp",
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Solve a scheduling problem using the specified solver.

    Args:
        jobs: List of jobs to be scheduled
        routes: List of available routes
        resources: List of available resources
        solver_type: Type of solver to use
        config: Optional configuration dictionary

    Returns:
        Dictionary containing the solution and metadata

    Raises:
        ValueError: If solver_type is not supported
    """
    solver = create_solver(solver_type, config)
    return solver.solve(jobs, routes, resources)


__all__ = ["create_solver", "solve_scheduling_problem", "BaseSolver", "CTPSolver"]
