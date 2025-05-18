"""
ExecutionMode module for representing different ways to execute operations.

This module provides the ExecutionMode class for managing different execution modes
of operations in the scheduling process. Each mode represents a specific way to
execute an operation with its own duration and resource requirements.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ExecutionMode:
    """Represents a specific way to execute an operation.

    An execution mode defines how an operation can be performed, including
    its duration and resource requirements. Different modes may represent
    different processing speeds, resource combinations, or quality levels.

    Attributes:
        id (str): Unique identifier for the execution mode
        job_id (str): ID of the job this mode belongs to
        duration (int): Time required to complete the operation in this mode
        resource_requirements (List[Dict[str, Any]]): List of required resources
        cost (float): Cost of executing in this mode
        quality_level (int): Quality level of the execution (higher is better)
        metadata (Dict[str, Any]): Additional metadata for the mode
    """

    id: str
    job_id: str
    duration: int
    resource_requirements: List[Dict[str, Any]] = field(default_factory=list)
    cost: float = 0.0
    quality_level: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate execution mode attributes after initialization."""
        if not isinstance(self.id, str) or not self.id:
            raise ValueError("id must be a non-empty string")
        if not isinstance(self.job_id, str) or not self.job_id:
            raise ValueError("job_id must be a non-empty string")
        if self.duration <= 0:
            raise ValueError("duration must be positive")
        if self.cost < 0:
            raise ValueError("cost must be non-negative")
        if self.quality_level < 1:
            raise ValueError("quality_level must be at least 1")

    def add_resource_requirement(self, resource_id: str, quantity: int = 1, setup_time: float = 0.0) -> None:
        """Add a resource requirement to this execution mode.

        Args:
            resource_id: ID of the required resource
            quantity: Number of units required
            setup_time: Setup time required for this resource

        Raises:
            ValueError: If quantity is not positive or setup_time is negative
        """
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        if setup_time < 0:
            raise ValueError("setup_time must be non-negative")

        requirement = {"resource_id": resource_id, "quantity": quantity, "setup_time": setup_time}
        self.resource_requirements.append(requirement)

    def get_total_setup_time(self) -> float:
        """Calculate the total setup time for all resources.

        Returns:
            float: Total setup time required
        """
        return sum(req.get("setup_time", 0.0) for req in self.resource_requirements)

    def get_total_cost(self) -> float:
        """Calculate the total cost of execution.

        Returns:
            float: Total cost including resource costs and mode cost
        """
        resource_costs = sum(req.get("cost", 0.0) for req in self.resource_requirements)
        return self.cost + resource_costs

    def is_valid(self) -> bool:
        """Check if this execution mode is valid.

        Returns:
            bool: True if the mode is valid, False otherwise
        """
        return self.id and self.job_id and self.duration > 0 and len(self.resource_requirements) > 0

    def __repr__(self) -> str:
        """Return a string representation of the execution mode."""
        return f"ExecutionMode(id={self.id}, " f"job_id={self.job_id}, " f"duration={self.duration})"

    def __str__(self) -> str:
        """Return a human-readable string representation of the execution mode."""
        return f"Execution Mode {self.id}: " f"Duration {self.duration}, " f"Quality Level {self.quality_level}"
