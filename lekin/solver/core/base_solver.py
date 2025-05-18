"""
Base solver interface for the LeKin scheduling system.
"""

from abc import ABC, abstractmethod
import logging
from typing import Any, Dict, Optional

from lekin.solver.core.problem import Problem
from lekin.solver.core.solution import Solution

logger = logging.getLogger(__name__)


class BaseSolver(ABC):
    """Abstract base class for all scheduling solvers."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the solver with optional configuration.

        Args:
            config: Optional configuration dictionary for solver parameters
        """
        self.config = config or {}
        self._validate_config()

    @abstractmethod
    def solve(self, problem: Problem) -> Solution:
        """Solve the scheduling problem.

        Args:
            problem: The scheduling problem to solve

        Returns:
            A solution to the problem

        Raises:
            ValueError: If the problem is invalid
            RuntimeError: If solving fails
        """
        pass

    @abstractmethod
    def validate_solution(self, solution: Solution) -> bool:
        """Validate if a solution meets all constraints.

        Args:
            solution: The solution to validate

        Returns:
            True if solution is valid, False otherwise
        """
        pass

    def _validate_config(self) -> None:
        """Validate the solver configuration.

        Raises:
            ValueError: If configuration is invalid
        """
        pass

    def get_solution_metrics(self, solution: Solution) -> Dict[str, float]:
        """Calculate key performance metrics for a solution.

        Args:
            solution: The solution to evaluate

        Returns:
            Dictionary of metric names and values
        """
        return {
            "makespan": solution.get_makespan(),
            "resource_utilization": sum(
                solution.get_resource_utilization(r.resource_id) for r in solution.problem.resources
            )
            / len(solution.problem.resources),
            "tardiness": solution.get_tardiness(),
        }

    def log_solution_metrics(self, solution: Solution) -> None:
        """Log the performance metrics of a solution.

        Args:
            solution: The solution to log metrics for
        """
        metrics = self.get_solution_metrics(solution)
        logger.info("Solution metrics:")
        for metric, value in metrics.items():
            logger.info(f"  {metric}: {value:.2f}")

    def save_solution(self, solution: Solution, filepath: str) -> None:
        """Save a solution to a file.

        Args:
            solution: The solution to save
            filepath: Path to save the solution to
        """
        import json

        with open(filepath, "w") as f:
            json.dump(solution.to_dict(), f, indent=2)

    @classmethod
    def load_solution(cls, filepath: str) -> Solution:
        """Load a solution from a file.

        Args:
            filepath: Path to load the solution from

        Returns:
            The loaded solution
        """
        import json

        with open(filepath, "r") as f:
            return Solution.from_dict(json.load(f))
