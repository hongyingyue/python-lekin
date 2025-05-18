"""
TimeSlot module for representing available time slots in job shop scheduling.

This module provides the TimeSlot class for managing time slots in the scheduling process.
A time slot represents a continuous period of time that can be assigned to operations.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, List, Optional, Union

import pandas as pd


@dataclass
class TimeSlot:
    """Represents a time slot in the scheduling process.

    A time slot is a continuous period of time that can be assigned to operations.
    It tracks its start time, end time, and any assigned operation.

    Attributes:
        start_time (datetime): Start time of the slot
        end_time (datetime): End time of the slot
        assigned_operation (Optional[Any]): Operation assigned to this slot, if any
        duration (timedelta): Duration of the time slot
        metadata (Dict[str, Any]): Additional metadata for the time slot
    """

    start_time: datetime
    end_time: datetime
    assigned_operation: Optional[Any] = None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        """Validate time slot attributes after initialization."""
        if not isinstance(self.start_time, datetime):
            raise TypeError("start_time must be a datetime object")
        if not isinstance(self.end_time, datetime):
            raise TypeError("end_time must be a datetime object")
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")

        self.duration = self.end_time - self.start_time

    def assign_operation(self, operation: Any, processing_time: Union[int, float]) -> None:
        """Assign an operation to this time slot.

        Args:
            operation: The operation to assign
            processing_time: Processing time in hours

        Raises:
            ValueError: If the time slot is already occupied
        """
        if self.is_occupied():
            raise ValueError("Time slot is already occupied")

        self.assigned_operation = operation
        self.end_time = self.start_time + timedelta(hours=float(processing_time))
        self.duration = self.end_time - self.start_time

    def is_occupied(self) -> bool:
        """Check if the time slot is occupied by an operation.

        Returns:
            bool: True if the slot is occupied, False otherwise
        """
        return self.assigned_operation is not None

    @property
    def hours(self) -> List[datetime]:
        """Get list of hours in this time slot.

        Returns:
            List[datetime]: List of datetime objects representing each hour
        """
        return pd.date_range(start=self.start_time, end=self.end_time, freq="1H").tolist()[:-1]

    @property
    def duration_of_hours(self) -> int:
        """Get the duration of the time slot in hours.

        Returns:
            int: Number of hours in the time slot
        """
        return len(pd.date_range(start=self.start_time, end=self.end_time, freq="1H")) - 1

    def overlaps_with(self, timeslot: "TimeSlot") -> float:
        """Calculate the overlap duration with another time slot.

        Args:
            timeslot: Another TimeSlot to check overlap with

        Returns:
            float: Overlap duration in hours, 0 if no overlap
        """
        if not isinstance(timeslot, TimeSlot):
            raise TypeError("timeslot must be a TimeSlot instance")

        overlap_start = max(self.start_time, timeslot.start_time)
        overlap_end = min(self.end_time, timeslot.end_time)

        if overlap_start < overlap_end:
            return (overlap_end - overlap_start).total_seconds() / 3600
        return 0.0

    def contains(self, time: datetime) -> bool:
        """Check if a given time falls within this time slot.

        Args:
            time: The time to check

        Returns:
            bool: True if the time is within this slot, False otherwise
        """
        return self.start_time <= time < self.end_time

    def split_at(self, time: datetime) -> tuple["TimeSlot", "TimeSlot"]:
        """Split this time slot at a given time.

        Args:
            time: The time at which to split the slot

        Returns:
            tuple[TimeSlot, TimeSlot]: Two new time slots

        Raises:
            ValueError: If the split time is not within this slot
        """
        if not self.contains(time):
            raise ValueError("Split time must be within the time slot")

        first_slot = TimeSlot(self.start_time, time)
        second_slot = TimeSlot(time, self.end_time)

        if self.is_occupied():
            first_slot.assigned_operation = self.assigned_operation

        return first_slot, second_slot

    def merge_with(self, timeslot: "TimeSlot") -> "TimeSlot":
        """Merge this time slot with another adjacent time slot.

        Args:
            timeslot: Another TimeSlot to merge with

        Returns:
            TimeSlot: A new merged time slot

        Raises:
            ValueError: If the time slots are not adjacent
        """
        if not isinstance(timeslot, TimeSlot):
            raise TypeError("timeslot must be a TimeSlot instance")

        if self.end_time != timeslot.start_time and self.start_time != timeslot.end_time:
            raise ValueError("Time slots must be adjacent to merge")

        start = min(self.start_time, timeslot.start_time)
        end = max(self.end_time, timeslot.end_time)

        merged = TimeSlot(start, end)
        if self.is_occupied():
            merged.assigned_operation = self.assigned_operation
        elif timeslot.is_occupied():
            merged.assigned_operation = timeslot.assigned_operation

        return merged

    def __repr__(self) -> str:
        """Get string representation of the time slot.

        Returns:
            str: String representation
        """
        return (
            f"TimeSlot(start_time={self.start_time}, end_time={self.end_time}, "
            f"duration={self.duration}, occupied={self.is_occupied()})"
        )

    def __eq__(self, other: object) -> bool:
        """Check if two time slots are equal.

        Args:
            other: Another object to compare with

        Returns:
            bool: True if the time slots are equal, False otherwise
        """
        if not isinstance(other, TimeSlot):
            return NotImplemented
        return (
            self.start_time == other.start_time
            and self.end_time == other.end_time
            and self.assigned_operation == other.assigned_operation
        )

    def __hash__(self) -> int:
        """Get hash value of the time slot.

        Returns:
            int: Hash value
        """
        return hash((self.start_time, self.end_time, self.assigned_operation))
