"""
Time slot management for scheduling operations.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional


@dataclass
class TimeSlot:
    """Represents a time slot for scheduling operations."""

    start_time: datetime
    end_time: datetime

    @property
    def duration(self) -> float:
        """Get the duration of the time slot in hours."""
        return (self.end_time - self.start_time).total_seconds() / 3600

    def overlaps_with(self, other: "TimeSlot") -> bool:
        """Check if this time slot overlaps with another.

        Args:
            other: Another time slot to check against

        Returns:
            True if time slots overlap, False otherwise
        """
        return self.start_time < other.end_time and self.end_time > other.start_time

    def contains(self, other: "TimeSlot") -> bool:
        """Check if this time slot completely contains another.

        Args:
            other: Another time slot to check against

        Returns:
            True if this time slot contains the other, False otherwise
        """
        return self.start_time <= other.start_time and self.end_time >= other.end_time

    def split(self, split_time: datetime) -> List["TimeSlot"]:
        """Split the time slot at a given time.

        Args:
            split_time: The time at which to split the slot

        Returns:
            List of two time slots if split is valid, empty list otherwise
        """
        if not (self.start_time < split_time < self.end_time):
            return []

        return [TimeSlot(self.start_time, split_time), TimeSlot(split_time, self.end_time)]

    def merge(self, other: "TimeSlot") -> Optional["TimeSlot"]:
        """Merge this time slot with another if they are adjacent or overlapping.

        Args:
            other: Another time slot to merge with

        Returns:
            Merged time slot if merge is possible, None otherwise
        """
        if not (self.overlaps_with(other) or self.end_time == other.start_time or self.start_time == other.end_time):
            return None

        return TimeSlot(min(self.start_time, other.start_time), max(self.end_time, other.end_time))

    def subtract(self, other: "TimeSlot") -> List["TimeSlot"]:
        """Subtract another time slot from this one.

        Args:
            other: Time slot to subtract

        Returns:
            List of remaining time slots
        """
        if not self.overlaps_with(other):
            return [self]

        result = []

        if self.start_time < other.start_time:
            result.append(TimeSlot(self.start_time, other.start_time))

        if self.end_time > other.end_time:
            result.append(TimeSlot(other.end_time, self.end_time))

        return result
