"""
Job module for representing manufacturing orders in a job shop scheduling problem.

This module provides the Job class and JobCollector for managing manufacturing orders
and their associated operations.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
import random
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

from lekin.lekin_struct.exceptions import SchedulingError, ValidationError
from lekin.lekin_struct.operation import Operation

random.seed(315)


@dataclass
class Job:
    """Represents a manufacturing order or production task.

    A job consists of a sequence of operations that need to be performed
    to complete the manufacturing process. Each job has properties like
    priority, quantity, and due date that influence its scheduling.

    Attributes:
        job_id (str): Unique identifier for the job
        job_name (Optional[str]): Human-readable name of the job
        priority (int): Priority level of the job (higher number = higher priority)
        quantity (int): Number of units to be produced
        demand_date (datetime): Due date for job completion
        job_type (str): Type/category of the job
        earliest_start_time (datetime): Earliest possible start time
        assigned_route_id (str): ID of the route assigned to this job
        assigned_bom_id (str): ID of the bill of materials
        current_operation_index (int): Index of the current operation
        _operations_sequence (List[Operation]): Sequence of operations for this job
    """

    job_id: str
    job_name: Optional[str] = None
    priority: int = 1
    quantity: int = 1
    demand_date: Optional[datetime] = None
    job_type: Optional[str] = None
    earliest_start_time: Optional[datetime] = None
    assigned_route_id: Optional[str] = None
    assigned_bom_id: Optional[str] = None
    current_operation_index: int = 0
    _operations_sequence: List[Operation] = field(default_factory=list)
    cached_scheduling: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate job attributes after initialization."""
        if not isinstance(self.job_id, str) or not self.job_id:
            raise ValidationError("job_id must be a non-empty string")
        if self.priority < 0:
            raise ValidationError("priority must be non-negative")
        if self.quantity <= 0:
            raise ValidationError("quantity must be positive")
        if self.demand_date and not isinstance(self.demand_date, datetime):
            raise ValidationError("demand_date must be a datetime object")
        if self.earliest_start_time and not isinstance(self.earliest_start_time, datetime):
            raise ValidationError("earliest_start_time must be a datetime object")

    @property
    def operations(self) -> List[Operation]:
        """Get the sequence of operations for this job."""
        return self._operations_sequence

    @operations.setter
    def operations(self, operations_sequence: List[Operation]) -> None:
        """Set the sequence of operations for this job.

        Args:
            operations_sequence: List of Operation objects
        """
        if not all(isinstance(op, Operation) for op in operations_sequence):
            raise ValidationError("All elements must be Operation instances")
        self._operations_sequence = operations_sequence

    def get_next_operation(self) -> Optional[Operation]:
        """Get the next operation to be processed.

        Returns:
            The next Operation in sequence, or None if all operations are complete
        """
        if self.current_operation_index < len(self._operations_sequence):
            return self._operations_sequence[self.current_operation_index]
        return None

    def assign_route(self, route_id: str) -> None:
        """Assign a route to this job.

        Args:
            route_id: ID of the route to assign
        """
        self.assigned_route_id = route_id

    def clear_cached_scheduling(
        self, all: bool = False, start: Optional[int] = None, direction: str = "forward"
    ) -> None:
        """Clear cached scheduling results.

        Args:
            all: If True, clear all cached results
            start: Starting operation index
            direction: Direction to clear ("forward" or "backward")
        """
        if all:
            self.cached_scheduling.clear()
        elif start is not None:
            if direction == "forward":
                keys_to_remove = [k for k in self.cached_scheduling if k >= start]
            else:
                keys_to_remove = [k for k in self.cached_scheduling if k <= start]
            for k in keys_to_remove:
                del self.cached_scheduling[k]

    def is_completed(self) -> bool:
        """Check if all operations in the job are completed.

        Returns:
            bool: True if all operations are completed, False otherwise
        """
        return self.current_operation_index >= len(self._operations_sequence)

    def get_remaining_operations(self) -> List[Operation]:
        """Get list of remaining operations to be processed.

        Returns:
            List[Operation]: List of remaining operations
        """
        return self._operations_sequence[self.current_operation_index :]

    def get_total_processing_time(self) -> float:
        """Calculate total processing time for all operations.

        Returns:
            float: Total processing time
        """
        return sum(op.processing_time for op in self._operations_sequence)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Job):
            return NotImplemented
        return self.job_id == other.job_id

    def __hash__(self) -> int:
        return hash(self.job_id)

    def __str__(self) -> str:
        return f"Job(id={self.job_id}, name={self.job_name})"

    def __repr__(self) -> str:
        return (
            f"Job(job_id='{self.job_id}', job_name='{self.job_name}', "
            f"priority={self.priority}, quantity={self.quantity})"
        )


@dataclass
class JobCollector:
    """Collection of jobs with additional management functionality.

    This class provides methods for managing a collection of jobs, including
    sorting, scheduling, and visualization utilities.

    Attributes:
        job_list (List[Job]): List of jobs in the collection
        color_dict (Dict[str, List[float]]): Dictionary mapping job IDs to colors
    """

    job_list: List[Job] = field(default_factory=list)
    color_dict: Dict[str, List[float]] = field(default_factory=dict)
    _index: int = field(default=-1, init=False)

    def __post_init__(self):
        """Validate job list after initialization."""
        if not all(isinstance(job, Job) for job in self.job_list):
            raise ValidationError("All elements in job_list must be Job instances")

    def __iter__(self) -> Iterator[Job]:
        """Return an iterator over the jobs."""
        self._index = -1
        return self

    def __next__(self) -> Job:
        """Get the next job in the iteration.

        Returns:
            Job: Next job in the collection

        Raises:
            StopIteration: When no more jobs are available
        """
        self._index += 1
        if self._index < len(self.job_list):
            return self.job_list[self._index]
        raise StopIteration("No more jobs available")

    def add_job(self, job: Job) -> None:
        """Add a job to the collection.

        Args:
            job: Job to add

        Raises:
            ValidationError: If job is not a Job instance
        """
        if not isinstance(job, Job):
            raise ValidationError("job must be a Job instance")
        self.job_list.append(job)

    def get_job_by_id(self, job_id: str) -> Optional[Job]:
        """Get a job by its ID.

        Args:
            job_id: ID of the job to find

        Returns:
            Optional[Job]: The job if found, None otherwise
        """
        for job in self.job_list:
            if job.job_id == job_id:
                return job
        return None

    def sort_jobs(self, jobs: Optional[List[Job]] = None) -> List[int]:
        """Sort jobs based on priority and demand date.

        Args:
            jobs: Optional list of jobs to sort. If None, uses all jobs.

        Returns:
            List[int]: Indices of sorted jobs
        """
        jobs_to_sort = jobs if jobs is not None else self.job_list

        def custom_sort(job: Job) -> Tuple[int, Optional[datetime]]:
            return (job.priority, job.demand_date)

        return [i[0] for i in sorted(enumerate(jobs_to_sort), key=lambda x: custom_sort(x[1]), reverse=False)]

    def get_schedule(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get the current schedule for all jobs.

        Returns:
            Dict[str, List[Dict[str, Any]]]: Schedule organized by resource
        """
        schedule = defaultdict(list)

        for job in self.job_list:
            for op in job.operations:
                if hasattr(op, "resource") and hasattr(op, "start_time"):
                    schedule[op.resource.id].append(
                        {"job_id": job.job_id, "operation_id": op.id, "start_time": op.start_time}
                    )

        return dict(schedule)

    def generate_color_list_for_jobs(self, pastel_factor: float = 0.5) -> Dict[str, List[float]]:
        """Generate distinct colors for job visualization.

        Args:
            pastel_factor: Factor to adjust color intensity (0.0 to 1.0)

        Returns:
            Dict[str, List[float]]: Dictionary mapping job IDs to RGB colors
        """
        for job in self.job_list:
            max_distance = None
            best_color = None

            for _ in range(100):
                color = [
                    (x + pastel_factor) / (1.0 + pastel_factor) for x in [random.uniform(0, 1.0) for _ in range(3)]
                ]

                if color not in self.color_dict.values():
                    best_color = color
                    break
                else:
                    best_distance = min(self.color_distance(color, c) for c in self.color_dict.values())
                    if not max_distance or best_distance > max_distance:
                        max_distance = best_distance
                        best_color = color

            self.color_dict[job.job_id] = best_color

        return self.color_dict

    @staticmethod
    def color_distance(c1: List[float], c2: List[float]) -> float:
        """Calculate the distance between two colors.

        Args:
            c1: First color as RGB list
            c2: Second color as RGB list

        Returns:
            float: Distance between colors
        """
        return sum(abs(x[0] - x[1]) for x in zip(c1, c2))
