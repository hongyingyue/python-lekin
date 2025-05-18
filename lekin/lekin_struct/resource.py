"""
Resource module for representing machines and workstations in job shop scheduling.

This module provides the Resource class and ResourceCollector for managing machines,
workstations, and other processing units in the scheduling process.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union

import numpy as np
import pandas as pd

from lekin.lekin_struct.exceptions import SchedulingError, ValidationError
from lekin.lekin_struct.timeslot import TimeSlot


class ResourceStatus(Enum):
    """Status of a resource in the scheduling process."""

    IDLE = "idle"
    BUSY = "busy"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"


@dataclass
class Resource:
    """Represents a machine, workstation, or other processing unit in the scheduling process.

    A resource can process operations and has constraints on its capacity and availability.
    It maintains a schedule of assigned operations and available time slots.

    Attributes:
        resource_id (str): Unique identifier for the resource
        resource_name (Optional[str]): Human-readable name of the resource
        max_tasks (int): Maximum number of tasks that can be processed simultaneously
        virtual_calendar (bool): Whether to use a virtual calendar for scheduling
        status (ResourceStatus): Current status of the resource
        efficiency (float): Resource efficiency factor (0.0 to 1.0)
        setup_time (float): Time required for setup between operations
        teardown_time (float): Time required for cleanup after operations
        maintenance_schedule (List[TimeSlot]): Scheduled maintenance periods
        metadata (Dict[str, Any]): Additional metadata for the resource
    """

    resource_id: str
    resource_name: Optional[str] = None
    max_tasks: int = 1
    virtual_calendar: bool = True
    status: ResourceStatus = field(default=ResourceStatus.IDLE)
    efficiency: float = field(default=1.0)
    setup_time: float = field(default=0.0)
    teardown_time: float = field(default=0.0)
    maintenance_schedule: List[TimeSlot] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Internal state
    _available_timeslots: List[TimeSlot] = field(default_factory=list, init=False)
    _available_hours: List[datetime] = field(default_factory=list, init=False)
    _assigned_operations: List[Any] = field(default_factory=list, init=False)
    _assigned_time_slots: List[TimeSlot] = field(default_factory=list, init=False)
    _assigned_hours: List[datetime] = field(default_factory=list, init=False)
    _continuous_empty_hours: List[int] = field(default_factory=list, init=False)
    _tasks: Dict[int, Optional[Any]] = field(default_factory=dict, init=False)
    _pending_list: List[Any] = field(default_factory=list, init=False)

    def __post_init__(self):
        """Validate resource attributes after initialization."""
        if not isinstance(self.resource_id, str) or not self.resource_id:
            raise ValidationError("resource_id must be a non-empty string")
        if self.max_tasks < 1:
            raise ValidationError("max_tasks must be positive")
        if not 0.0 <= self.efficiency <= 1.0:
            raise ValidationError("efficiency must be between 0.0 and 1.0")
        if self.setup_time < 0 or self.teardown_time < 0:
            raise ValidationError("setup_time and teardown_time must be non-negative")

        # Initialize tasks dictionary
        self._tasks = {i: None for i in range(1, self.max_tasks + 1)}

    @property
    def available_timeslots(self) -> List[TimeSlot]:
        """Get available time slots for this resource."""
        return self._available_timeslots

    @property
    def available_hours(self) -> List[datetime]:
        """Get available hours for this resource."""
        return self._available_hours

    @available_hours.setter
    def available_hours(self, hours: List[datetime]) -> None:
        """Set available hours for this resource.

        Args:
            hours: List of available hours
        """
        if not all(isinstance(h, datetime) for h in hours):
            raise ValidationError("All hours must be datetime objects")
        self._available_hours = sorted(hours)
        self.update_continuous_empty_hours()

    def add_timeslot(self, start_time: datetime, end_time: datetime) -> None:
        """Add an available time slot to the resource.

        Args:
            start_time: Start time of the slot
            end_time: End time of the slot
        """
        if not isinstance(start_time, datetime) or not isinstance(end_time, datetime):
            raise ValidationError("start_time and end_time must be datetime objects")
        if start_time >= end_time:
            raise ValidationError("start_time must be before end_time")

        timeslot = TimeSlot(start_time, end_time)
        self._available_timeslots.append(timeslot)
        self._available_timeslots.sort(key=lambda x: x.start_time)

    def add_available_hours(self, hours: List[datetime]) -> None:
        """Add available hours to the resource.

        Args:
            hours: List of available hours
        """
        if not all(isinstance(h, datetime) for h in hours):
            raise ValidationError("All hours must be datetime objects")
        self._available_hours = sorted(set(self._available_hours + hours))
        self.update_continuous_empty_hours()

    def update_continuous_empty_hours(self) -> None:
        """Update the continuous empty hours tracking."""
        if not self._available_hours:
            self._continuous_empty_hours = []
            return

        empty_hours = []
        continuous_hours = 0

        for hour in self._available_hours:
            if hour in self._assigned_hours:
                continuous_hours = 0
            else:
                continuous_hours += 1
            empty_hours.append(continuous_hours)

        self._continuous_empty_hours = empty_hours

    def get_available_timeslot_for_op(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        periods: Optional[int] = None,
        freq: str = "1H",
        forward: bool = True,
    ) -> List[datetime]:
        """Get available time slots for an operation.

        Args:
            start: Start time constraint
            end: End time constraint
            periods: Number of periods needed
            freq: Frequency of time slots
            forward: Whether to search forward in time

        Returns:
            List of available hours that meet the constraints
        """
        if not periods:
            return []

        self.update_continuous_empty_hours()
        select_hours = [h for h in self._available_hours if not end or h <= end]

        if not select_hours:
            return []

        front_available = self._continuous_empty_hours[: len(select_hours)]

        if forward:
            chosen_hours_index = self._find_first_index_larger(periods, front_available)
        else:
            chosen_hours_index = self._find_last_index_larger(periods, front_available)

        if not chosen_hours_index:
            back_available = self._continuous_empty_hours[len(select_hours) :]
            chosen_hours_index = self._find_first_index_larger(periods, back_available)

        if chosen_hours_index:
            chosen_hours = self._available_hours[int(chosen_hours_index - periods) : chosen_hours_index]
            return chosen_hours

        return []

    def get_earliest_available_time(
        self, duration: Optional[int] = None, start: Optional[datetime] = None
    ) -> Optional[datetime]:
        """Get the earliest available time for an operation.

        Args:
            duration: Required duration
            start: Start time constraint

        Returns:
            Earliest available time or None if not available
        """
        available = set(self._available_hours) - set(self._assigned_hours)
        if start:
            available = {h for h in available if h >= start}
        return min(available) if available else None

    def get_latest_available_time(
        self, duration: Optional[int] = None, end: Optional[datetime] = None
    ) -> Optional[datetime]:
        """Get the latest available time for an operation.

        Args:
            duration: Required duration
            end: End time constraint

        Returns:
            Latest available time or None if not available
        """
        self.update_continuous_empty_hours()
        if not end:
            end = max(self._available_hours) if self._available_hours else None

        if not end or not duration:
            return None

        available = [i + 1 for i, v in enumerate(self._continuous_empty_hours[:end]) if v >= duration]
        return max(available) if available else None

    def is_available(self, start_time: datetime, end_time: datetime) -> bool:
        """Check if the resource is available during the specified time period.

        Args:
            start_time: Start time to check
            end_time: End time to check

        Returns:
            True if available, False otherwise
        """
        if not isinstance(start_time, datetime) or not isinstance(end_time, datetime):
            raise ValidationError("start_time and end_time must be datetime objects")
        if start_time >= end_time:
            raise ValidationError("start_time must be before end_time")

        for assigned_slot in self._assigned_time_slots:
            if not (end_time <= assigned_slot.start_time or start_time >= assigned_slot.end_time):
                return False
        return True

    def assign_operation(self, operation: Any, start_time: datetime, end_time: datetime) -> None:
        """Assign an operation to the resource.

        Args:
            operation: Operation to assign
            start_time: Start time of the operation
            end_time: End time of the operation
        """
        if not self.is_available(start_time, end_time):
            raise SchedulingError("Resource is not available during the specified time")

        timeslot = TimeSlot(start_time, end_time)
        timeslot.assign_operation(operation, (end_time - start_time).total_seconds() / 3600)

        self._assigned_operations.append(operation)
        self._assigned_time_slots.append(timeslot)
        self._assigned_hours.extend(pd.date_range(start_time, end_time, freq="H"))
        self.update_continuous_empty_hours()

    def _find_first_index_larger(self, value: int, lst: List[int]) -> Optional[int]:
        """Find the first index in a list where the value is larger than the input.

        Args:
            value: Value to compare against
            lst: List to search in

        Returns:
            Index of first larger value or None if not found
        """
        for i, v in enumerate(lst):
            if v > value:
                return i
        return None

    def _find_last_index_larger(self, value: int, lst: List[int]) -> Optional[int]:
        """Find the last index in a list where the value is larger than the input.

        Args:
            value: Value to compare against
            lst: List to search in

        Returns:
            Index of last larger value or None if not found
        """
        for i, v in enumerate(reversed(lst)):
            if v > value:
                return len(lst) - i
        return None

    def __hash__(self) -> int:
        return hash(self.resource_id)

    def __str__(self) -> str:
        return f"{self.resource_id}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Resource):
            return NotImplemented
        return self.resource_id == other.resource_id

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Resource):
            return NotImplemented
        return self.resource_id < other.resource_id

    def __repr__(self) -> str:
        return (
            f"Resource(resource_id='{self.resource_id}', "
            f"resource_name='{self.resource_name}', "
            f"max_tasks={self.max_tasks})"
        )


@dataclass
class ResourceCollector:
    """Collection of resources with additional management functionality.

    This class provides methods for managing a collection of resources, including
    scheduling, capacity planning, and maintenance coordination.

    Attributes:
        resources (Dict[str, Resource]): Dictionary of resources indexed by ID
    """

    resources: Dict[str, Resource] = field(default_factory=dict)
    _index: int = field(default=-1, init=False)

    def __post_init__(self):
        """Validate resources after initialization."""
        if not all(isinstance(r, Resource) for r in self.resources.values()):
            raise ValidationError("All values in resources must be Resource instances")

    def __iter__(self):
        """Return an iterator over the resources."""
        self._index = -1
        return self

    def __next__(self) -> Resource:
        """Get the next resource in the iteration.

        Returns:
            Next resource in the collection

        Raises:
            StopIteration: When no more resources are available
        """
        self._index += 1
        if self._index < len(self.resources):
            return list(self.resources.values())[self._index]
        raise StopIteration("No more resources available")

    def add_resource(self, resource: Resource) -> None:
        """Add a resource to the collection.

        Args:
            resource: Resource to add

        Raises:
            ValidationError: If resource is not a Resource instance
        """
        if not isinstance(resource, Resource):
            raise ValidationError("resource must be a Resource instance")
        self.resources[resource.resource_id] = resource

    def get_resource_by_id(self, resource_id: str) -> Optional[Resource]:
        """Get a resource by its ID.

        Args:
            resource_id: ID of the resource to find

        Returns:
            The resource if found, None otherwise
        """
        return self.resources.get(resource_id)

    def get_all_resources(self) -> List[Resource]:
        """Get all resources in the collection.

        Returns:
            List of all resources
        """
        return list(self.resources.values())

    def get_available_resources(self, start_time: datetime, end_time: datetime) -> List[Resource]:
        """Get resources that are available during the specified time period.

        Args:
            start_time: Start time to check
            end_time: End time to check

        Returns:
            List of available resources
        """
        return [r for r in self.resources.values() if r.is_available(start_time, end_time)]

    def get_resource_utilization(self, start_time: datetime, end_time: datetime) -> Dict[str, float]:
        """Calculate resource utilization during the specified time period.

        Args:
            start_time: Start time of the period
            end_time: End time of the period

        Returns:
            Dictionary mapping resource IDs to utilization percentages
        """
        total_hours = (end_time - start_time).total_seconds() / 3600
        utilization = {}

        for resource in self.resources.values():
            assigned_hours = sum(1 for h in resource._assigned_hours if start_time <= h <= end_time)
            utilization[resource.resource_id] = assigned_hours / total_hours if total_hours > 0 else 0.0

        return utilization
