"""
Allocation module for representing operation assignments in job shop scheduling.

This module provides the Allocation class for managing the assignment of operations
to resources and time slots in the scheduling process.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, List, Optional

if TYPE_CHECKING:
    from .execution_mode import ExecutionMode
    from .operation import Operation


@dataclass
class Allocation:
    """Represents an assignment of an operation to a resource and time slot.

    An allocation defines when and how an operation will be executed, including
    its execution mode, timing constraints, and dependencies on other allocations.

    Attributes:
        id (str): Unique identifier for the allocation
        operation (Operation): The operation being allocated
        execution_mode (Optional[ExecutionMode]): The chosen execution mode
        delay (Optional[int]): Delay before starting the operation
        predecessors (List[Allocation]): Allocations that must complete before this one
        successors (List[Allocation]): Allocations that must start after this one
        start_date (Optional[int]): Calculated start date of the operation
        end_date (Optional[int]): Calculated end date of the operation
        busy_dates (List[int]): List of dates when the operation is being processed
        status (str): Current status of the allocation
        assigned_resource (Optional[str]): ID of the resource assigned to this allocation
    """

    id: str
    operation: "Operation"
    execution_mode: Optional["ExecutionMode"] = None
    delay: Optional[int] = None
    predecessors: List["Allocation"] = field(default_factory=list)
    successors: List["Allocation"] = field(default_factory=list)
    start_date: Optional[int] = None
    end_date: Optional[int] = None
    busy_dates: List[int] = field(default_factory=list)
    status: str = "pending"
    assigned_resource: Optional[str] = None

    def __post_init__(self):
        """Validate allocation attributes after initialization."""
        if not isinstance(self.id, str) or not self.id:
            raise ValueError("id must be a non-empty string")
        if not hasattr(self.operation, "id"):
            raise ValueError("operation must be a valid Operation instance")

    def set_execution_mode(self, mode: "ExecutionMode") -> None:
        """Set the execution mode for this allocation.

        Args:
            mode: The execution mode to set

        Raises:
            ValueError: If mode is not a valid ExecutionMode instance
        """
        if not hasattr(mode, "duration"):
            raise ValueError("mode must be a valid ExecutionMode instance")
        self.execution_mode = mode
        self.invalidate_computed_variables()

    def set_delay(self, delay: int) -> None:
        """Set the delay before starting the operation.

        Args:
            delay: The delay value to set

        Raises:
            ValueError: If delay is negative
        """
        if delay < 0:
            raise ValueError("delay must be non-negative")
        self.delay = delay
        self.invalidate_computed_variables()

    def invalidate_computed_variables(self) -> None:
        """Invalidate all computed timing variables."""
        self.start_date = None
        self.end_date = None
        self.busy_dates = []
        self.status = "pending"

    def compute_dates(self) -> None:
        """Compute the start date, end date, and busy dates for this allocation.

        This method calculates the timing information based on the execution mode
        and delay. It should be called after setting the execution mode and delay.
        """
        if self.execution_mode and self.delay is not None:
            self.start_date = self.delay
            self.end_date = self.start_date + self.execution_mode.duration
            self.busy_dates = list(range(self.start_date, self.end_date))
            self.status = "scheduled"

    def add_predecessor(self, allocation: "Allocation") -> None:
        """Add a predecessor allocation.

        Args:
            allocation: The predecessor allocation to add

        Raises:
            ValueError: If allocation is not a valid Allocation instance
        """
        if not isinstance(allocation, Allocation):
            raise ValueError("allocation must be an Allocation instance")
        if allocation not in self.predecessors:
            self.predecessors.append(allocation)
            if self not in allocation.successors:
                allocation.successors.append(self)

    def add_successor(self, allocation: "Allocation") -> None:
        """Add a successor allocation.

        Args:
            allocation: The successor allocation to add

        Raises:
            ValueError: If allocation is not a valid Allocation instance
        """
        if not isinstance(allocation, Allocation):
            raise ValueError("allocation must be an Allocation instance")
        if allocation not in self.successors:
            self.successors.append(allocation)
            if self not in allocation.predecessors:
                allocation.predecessors.append(self)

    def is_valid(self) -> bool:
        """Check if this allocation is valid.

        Returns:
            bool: True if the allocation is valid, False otherwise
        """
        return (
            self.execution_mode is not None
            and self.delay is not None
            and self.start_date is not None
            and self.end_date is not None
        )

    def __repr__(self) -> str:
        """Return a string representation of the allocation."""
        return f"Allocation(id={self.id}, " f"operation={self.operation.id}, " f"status={self.status})"

    def __str__(self) -> str:
        """Return a human-readable string representation of the allocation."""
        return f"Allocation {self.id}: " f"Operation {self.operation.id} " f"({self.status})"
