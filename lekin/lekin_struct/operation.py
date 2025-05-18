"""
Operation Struct
Represents a manufacturing operation in a job shop scheduling problem.

This module provides the core data structures for representing operations in a job shop scheduling problem.
An operation represents a specific manufacturing step that needs to be performed on a resource.

Classes:
    Operation: Represents a single manufacturing operation
    JobOperations: Represents a collection of operations from the same job
    MaterialOperation: Represents operations grouped by material
    OperationCollector: Manages collections of operations
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional, Tuple, Union

if TYPE_CHECKING:
    from .allocation import Allocation
    from .execution_mode import ExecutionMode


class OperationStatus(Enum):
    """Status of an operation in the scheduling process."""

    NONE = "none"
    WAITING = "waiting"
    PENDING = "pending"
    DONE = "done"


@dataclass
class Operation:
    """Represents a single manufacturing operation in a job shop scheduling problem.

    Attributes:
        operation_id (str): Unique identifier for the operation
        operation_name (str): Human-readable name of the operation
        quantity (int): Number of units to be processed
        processing_time (Union[int, List[int], float, List[float]]): Time required to complete the operation
        pre_time (float): Setup time required before the operation
        post_time (float): Cleanup time required after the operation
        lead_time (float): Minimum time required between operations
        lag_time (float): Maximum time allowed between operations
        route_constraint (Optional[Any]): Constraints on the route this operation can take
        available_resource (Optional[List[str]]): List of resource IDs that can perform this operation
        available_resource_priority (Optional[List[int]]): Priority order for resource selection
        parent_job_id (Optional[str]): ID of the job this operation belongs to
        prev_operation_ids (Optional[List[str]]): IDs of predecessor operations
        next_operation_ids (Optional[List[str]]): IDs of successor operations
    """

    operation_id: str
    operation_name: str
    quantity: int
    processing_time: Union[int, List[int], float, List[float]]
    pre_time: float = 0
    post_time: float = 0
    lead_time: float = 0
    lag_time: float = 0
    route_constraint: Optional[Any] = None
    available_resource: Optional[List[str]] = None
    available_resource_priority: Optional[List[int]] = None
    parent_job_id: Optional[str] = None
    prev_operation_ids: Optional[List[str]] = None
    next_operation_ids: Optional[List[str]] = None

    # Scheduling state
    earliest_start_time: Optional[datetime] = None
    latest_start_time: Optional[datetime] = None
    earliest_end_time: Optional[datetime] = None
    latest_end_time: Optional[datetime] = None

    # Assignment state
    status: OperationStatus = field(default=OperationStatus.NONE)
    assigned_resource: Optional[str] = None
    assigned_time_slot: Optional[Any] = None

    # Execution modes and allocations
    execution_modes: List["ExecutionMode"] = field(default_factory=list)
    allocations: List["Allocation"] = field(default_factory=list)

    def __post_init__(self):
        """Validate operation attributes after initialization."""
        if not isinstance(self.operation_id, str) or not self.operation_id:
            raise ValueError("operation_id must be a non-empty string")
        if not isinstance(self.operation_name, str):
            raise ValueError("operation_name must be a string")
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")
        if isinstance(self.processing_time, (int, float)) and self.processing_time < 0:
            raise ValueError("processing_time must be non-negative")
        if self.pre_time < 0 or self.post_time < 0:
            raise ValueError("pre_time and post_time must be non-negative")
        if self.lead_time < 0 or self.lag_time < 0:
            raise ValueError("lead_time and lag_time must be non-negative")

    def calculate_granularity_metric(self, available_time_slot: Any) -> float:
        """Calculate granularity metric based on processing time and available time slot.

        Args:
            available_time_slot: The available time slot for scheduling

        Returns:
            float: Granularity metric value
        """
        if not available_time_slot:
            return float("inf")

        processing_time = (
            self.processing_time if isinstance(self.processing_time, (int, float)) else sum(self.processing_time)
        )
        available_duration = available_time_slot.duration

        return processing_time / available_duration if available_duration > 0 else float("inf")

    def is_finished(self) -> bool:
        """Check if the operation has been completed.

        Returns:
            bool: True if the operation has been assigned to a resource
        """
        return self.assigned_resource is not None

    def add_execution_mode(self, mode: "ExecutionMode") -> None:
        """Add an execution mode to the operation.

        Args:
            mode: The execution mode to add
        """
        if not isinstance(mode, ExecutionMode):
            raise TypeError("mode must be an ExecutionMode instance")
        self.execution_modes.append(mode)

    def add_allocation(self, allocation: "Allocation") -> None:
        """Add an allocation to the operation.

        Args:
            allocation: The allocation to add
        """
        if not isinstance(allocation, Allocation):
            raise TypeError("allocation must be an Allocation instance")
        self.allocations.append(allocation)

    def __repr__(self) -> str:
        return f"Operation(id={self.operation_id}, name={self.operation_name})"

    def __str__(self) -> str:
        return f"{self.operation_id}-{self.operation_name}"


@dataclass
class JobOperations:
    """Represents a collection of operations from the same job.

    This class manages a sequence of operations that belong to the same job,
    providing methods to access and manipulate the operation sequence.

    Attributes:
        operations (List[Operation]): List of operations in the job
        job_id (str): ID of the parent job
    """

    operations: List[Operation] = field(default_factory=list)
    job_id: Optional[str] = None

    def __post_init__(self):
        """Validate job operations after initialization."""
        if not all(isinstance(op, Operation) for op in self.operations):
            raise TypeError("All operations must be Operation instances")
        if self.job_id:
            for op in self.operations:
                op.parent_job_id = self.job_id

    @property
    def job(self) -> Optional[str]:
        """Get the parent job ID.

        Returns:
            Optional[str]: The parent job ID
        """
        return self.job_id

    def add_operation(self, operation: Operation) -> None:
        """Add an operation to the job sequence.

        Args:
            operation: The operation to add
        """
        if not isinstance(operation, Operation):
            raise TypeError("operation must be an Operation instance")
        if self.job_id:
            operation.parent_job_id = self.job_id
        self.operations.append(operation)

    def get_operation_by_id(self, operation_id: str) -> Optional[Operation]:
        """Get an operation by its ID.

        Args:
            operation_id: The ID of the operation to find

        Returns:
            Optional[Operation]: The found operation or None
        """
        return next((op for op in self.operations if op.operation_id == operation_id), None)

    def get_next_operation(self, current_operation_id: str) -> Optional[Operation]:
        """Get the next operation in sequence after the given operation.

        Args:
            current_operation_id: The ID of the current operation

        Returns:
            Optional[Operation]: The next operation or None if it's the last operation
        """
        current_op = self.get_operation_by_id(current_operation_id)
        if not current_op or not current_op.next_operation_ids:
            return None
        return self.get_operation_by_id(current_op.next_operation_ids[0])


@dataclass
class MaterialOperation:
    """Represents operations grouped by material in the scheduling process.

    This class manages operations that share the same material, providing
    methods to handle material-specific scheduling constraints and requirements.

    Attributes:
        material_id (str): ID of the material
        job_operations (List[JobOperations]): List of job operations using this material
    """

    material_id: str
    job_operations: List[JobOperations] = field(default_factory=list)

    def __post_init__(self):
        """Validate material operation after initialization."""
        if not isinstance(self.material_id, str) or not self.material_id:
            raise ValueError("material_id must be a non-empty string")
        if not all(isinstance(jo, JobOperations) for jo in self.job_operations):
            raise TypeError("All job operations must be JobOperations instances")

    @property
    def material(self) -> str:
        """Get the material ID.

        Returns:
            str: The material ID
        """
        return self.material_id

    def add_job_operations(self, job_operations: JobOperations) -> None:
        """Add job operations to this material operation.

        Args:
            job_operations: The job operations to add
        """
        if not isinstance(job_operations, JobOperations):
            raise TypeError("job_operations must be a JobOperations instance")
        self.job_operations.append(job_operations)

    def get_all_operations(self) -> List[Operation]:
        """Get all operations across all job operations.

        Returns:
            List[Operation]: List of all operations
        """
        return [op for jo in self.job_operations for op in jo.operations]

    def get_operations_by_job_id(self, job_id: str) -> List[Operation]:
        """Get operations for a specific job.

        Args:
            job_id: The ID of the job

        Returns:
            List[Operation]: List of operations for the specified job
        """
        for jo in self.job_operations:
            if jo.job_id == job_id:
                return jo.operations
        return []


@dataclass
class OperationCollector:
    """Manages collections of operations in the scheduling system.

    This class provides methods to store, retrieve, and manage operations
    across different jobs and routes. It maintains a centralized registry
    of all operations for efficient access and management.

    Attributes:
        operation_list (List[Operation]): List of all operations
        _operation_map (Dict[str, Operation]): Map of operation IDs to operations
    """

    operation_list: List[Operation] = field(default_factory=list)
    _operation_map: Dict[str, Operation] = field(default_factory=dict, init=False)

    def __post_init__(self):
        """Initialize the operation map from the operation list."""
        self._operation_map = {op.operation_id: op for op in self.operation_list}

    def add_operation(self, operation: Operation) -> None:
        """Add an operation to the collector.

        Args:
            operation: The operation to add
        """
        if not isinstance(operation, Operation):
            raise TypeError("operation must be an Operation instance")
        if operation.operation_id in self._operation_map:
            raise ValueError(f"Operation with ID {operation.operation_id} already exists")

        self.operation_list.append(operation)
        self._operation_map[operation.operation_id] = operation

    def get_operation_by_id(self, operation_id: str) -> Optional[Operation]:
        """Get an operation by its ID.

        Args:
            operation_id: The ID of the operation to find

        Returns:
            Optional[Operation]: The found operation or None
        """
        return self._operation_map.get(operation_id)

    def get_operations_by_job_and_route(self, job_list: List[Any], route_list: List[Any]) -> List[Operation]:
        """Get operations for a list of jobs and their corresponding routes.

        Args:
            job_list: List of jobs
            route_list: List of routes corresponding to the jobs

        Returns:
            List[Operation]: List of operations for the specified jobs and routes

        Raises:
            ValueError: If job_list and route_list have different lengths
        """
        if len(job_list) != len(route_list):
            raise ValueError("job_list and route_list must have the same length")

        operations = []
        for job, route in zip(job_list, route_list):
            job_operations = route.get_operations()

            # Set up operation relationships
            for i, operation in enumerate(job_operations):
                if i > 0:
                    operation.prev_operation_ids = [job_operations[i - 1].operation_id]
                if i < len(job_operations) - 1:
                    operation.next_operation_ids = [job_operations[i + 1].operation_id]

                operation.parent_job_id = job.job_id
                operations.append(operation)

                # Add to collector if not already present
                if operation.operation_id not in self._operation_map:
                    self.add_operation(operation)

            # Assign operations to job
            job.operations = job_operations

        return operations

    def get_operations_by_job_id(self, job_id: str) -> List[Operation]:
        """Get all operations for a specific job.

        Args:
            job_id: The ID of the job

        Returns:
            List[Operation]: List of operations for the specified job
        """
        return [op for op in self.operation_list if op.parent_job_id == job_id]

    def get_operations_by_resource_id(self, resource_id: str) -> List[Operation]:
        """Get all operations that can be performed by a specific resource.

        Args:
            resource_id: The ID of the resource

        Returns:
            List[Operation]: List of operations that can be performed by the resource
        """
        return [op for op in self.operation_list if op.available_resource and resource_id in op.available_resource]

    def clear(self) -> None:
        """Clear all operations from the collector."""
        self.operation_list.clear()
        self._operation_map.clear()

    def __len__(self) -> int:
        """Get the number of operations in the collector.

        Returns:
            int: Number of operations
        """
        return len(self.operation_list)

    def __iter__(self) -> Iterator[Operation]:
        """Iterate over all operations in the collector.

        Returns:
            Iterator[Operation]: Iterator over operations
        """
        return iter(self.operation_list)
