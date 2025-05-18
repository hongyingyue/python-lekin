"""Flexible job shop scheduler with support for multiple scheduling types and objectives.

This module provides a flexible scheduling framework that supports:
- Different scheduling types (job shop, flow shop, open shop)
- Multiple objectives (makespan, tardiness, etc.)
- Various solving methods (heuristics, meta-heuristics, exact methods)
- Visualization and evaluation capabilities
"""

from abc import ABC, abstractmethod
from collections import OrderedDict
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from lekin.datasets.check_data import check_data
from lekin.solver import BaseSolver

logger = logging.getLogger(__name__)


class Scheduler(ABC):
    """Base class for all schedulers.

    This class provides a common interface for different types of schedulers
    and implements shared functionality.
    """

    def __init__(
        self,
        objective: "BaseObjective",
        solver: BaseSolver,
        max_operations: int,
        scheduling_type: str = "job_shop",
        **kwargs,
    ):
        """Initialize the scheduler.

        Args:
            objective: The objective function to optimize
            solver: The solver to use for finding solutions
            max_operations: Maximum number of operations per job
            scheduling_type: Type of scheduling problem ("job_shop", "flow_shop", "open_shop")
            **kwargs: Additional configuration parameters
        """
        self.objective = objective
        self.solver = solver
        self.max_operations = max_operations
        self.scheduling_type = scheduling_type
        self.config = kwargs
        self.solution = None
        self.metrics = {}

        # Validate scheduling type
        valid_types = ["job_shop", "flow_shop", "open_shop"]
        if scheduling_type not in valid_types:
            raise ValueError(f"Scheduling type must be one of {valid_types}")

        logger.info(f"Initialized {scheduling_type} scheduler with {solver.__class__.__name__}")

    def run(self, jobs: List[Dict], machines: List[Dict]) -> Dict:
        """Run the scheduling algorithm.

        Args:
            jobs: List of jobs with their operations and requirements
            machines: List of available machines and their capabilities

        Returns:
            Dict containing the scheduling solution
        """
        # Validate input data
        check_data(jobs, machines)

        # Solve the scheduling problem
        self.solution = self.solver.solve(jobs, machines)

        # Evaluate the solution
        self.evaluate()

        return self.solution

    def evaluate(self) -> Dict[str, float]:
        """Evaluate the current solution using the objective function.

        Returns:
            Dict containing evaluation metrics
        """
        if self.solution is None:
            raise ValueError("No solution available. Run the scheduler first.")

        self.metrics = self.objective.evaluate(self.solution)
        logger.info(f"Solution evaluation: {self.metrics}")
        return self.metrics

    def plot(self, save_path: Optional[str] = None) -> None:
        """Plot the current solution.

        Args:
            save_path: Optional path to save the plot
        """
        if self.solution is None:
            raise ValueError("No solution available. Run the scheduler first.")

        self.solver.plot(self.solution, save_path=save_path)

    @abstractmethod
    def validate_solution(self, solution: Dict) -> bool:
        """Validate if a solution satisfies all constraints.

        Args:
            solution: The solution to validate

        Returns:
            bool indicating if the solution is valid
        """
        pass

    def get_metrics(self) -> Dict[str, float]:
        """Get the current evaluation metrics.

        Returns:
            Dict containing the metrics
        """
        return self.metrics.copy()

    def reset(self) -> None:
        """Reset the scheduler state."""
        self.solution = None
        self.metrics = {}
