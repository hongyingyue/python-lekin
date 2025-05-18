"""
Base constraint system for scheduling problems.
"""

from abc import ABC, abstractmethod
import logging
from typing import Any, Dict, List, Optional

from lekin.solver.core.solution import Solution

logger = logging.getLogger(__name__)


class BaseConstraint(ABC):
    """Base class for all scheduling constraints."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the constraint.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._validate_config()

    @abstractmethod
    def check(self, solution: Solution) -> bool:
        """Check if the solution satisfies this constraint.

        Args:
            solution: The solution to check

        Returns:
            True if constraint is satisfied, False otherwise
        """
        pass

    def _validate_config(self) -> None:
        """Validate the constraint configuration.

        Raises:
            ValueError: If configuration is invalid
        """
        pass

    def get_violations(self, solution: Solution) -> List[Dict[str, Any]]:
        """Get detailed information about constraint violations.

        Args:
            solution: The solution to check

        Returns:
            List of violation details
        """
        return []


class ConstraintManager:
    """Manages a collection of constraints."""

    def __init__(self):
        """Initialize the constraint manager."""
        self.constraints: List[BaseConstraint] = []

    def add_constraint(self, constraint: BaseConstraint) -> None:
        """Add a constraint to the manager.

        Args:
            constraint: The constraint to add
        """
        self.constraints.append(constraint)

    def check_all(self, solution: Solution) -> bool:
        """Check if a solution satisfies all constraints.

        Args:
            solution: The solution to check

        Returns:
            True if all constraints are satisfied, False otherwise
        """
        try:
            return all(constraint.check(solution) for constraint in self.constraints)
        except Exception as e:
            logger.error(f"Error checking constraints: {str(e)}")
            return False

    def get_all_violations(self, solution: Solution) -> List[Dict[str, Any]]:
        """Get all constraint violations in a solution.

        Args:
            solution: The solution to check

        Returns:
            List of all constraint violations
        """
        violations = []
        for constraint in self.constraints:
            if not constraint.check(solution):
                violations.extend(constraint.get_violations(solution))
        return violations

    def log_violations(self, solution: Solution) -> None:
        """Log all constraint violations in a solution.

        Args:
            solution: The solution to check
        """
        violations = self.get_all_violations(solution)
        if violations:
            logger.warning(f"Found {len(violations)} constraint violations:")
            for violation in violations:
                logger.warning(f"  - {violation}")
        else:
            logger.info("No constraint violations found")
