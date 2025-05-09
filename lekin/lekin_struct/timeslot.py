"""
Calendar for resource Struct
"""

from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple, Type, Union

import pandas as pd


class TimeSlot(object):
    def __init__(self, start_time, end_time, **kwargs):
        self.start_time = start_time
        self.end_time = end_time
        self.duration = end_time - start_time
        self.assigned_operation = None

        for key, value in kwargs.items():
            setattr(self, key, value)

    def assign_operation(self, operation, processing_time):
        self.assigned_operation = operation
        self.end_time = self.start_time + timedelta(hours=processing_time)

    def is_occupied(self):
        return self.assigned_operation is not None

    @property
    def hours(self):
        return pd.date_range(start=self.start_time, end=self.end_time, freq="1H").tolist()[:-1]

    @property
    def duration_of_hours(self):
        return len(pd.date_range(start=self.start_time, end=self.end_time, freq="1H")) - 1

    def overlaps_with(self, timeslot):
        overlap_start = max(self.start_time, timeslot.start_time)
        overlap_end = min(self.end_time, timeslot.end_time)

        if overlap_start < overlap_end:
            overlap_hours = (overlap_end - overlap_start).total_seconds() / 3600
            return overlap_hours
        else:
            return 0

    def __repr__(self):
        return f"TimeSlot(start_date={self.start_date}, end_date={self.end_date})"
