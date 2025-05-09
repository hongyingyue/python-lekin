from typing import TYPE_CHECKING, List, Optional


class Allocation:
    def __init__(self, id: str, operation):
        self.id = id
        self.op = operation
        self.execution_mode: Optional = None
        self.delay: Optional[int] = None
        self.predecessors: List["Allocation"] = []
        self.successors: List["Allocation"] = []
        self.start_date: Optional[int] = None
        self.end_date: Optional[int] = None
        self.busy_dates: List[int] = []

    def set_execution_mode(self, mode):
        self.execution_mode = mode
        self.invalidate_computed_variables()

    def set_delay(self, delay: int):
        self.delay = delay
        self.invalidate_computed_variables()

    def invalidate_computed_variables(self):
        self.start_date = None
        self.end_date = None
        self.busy_dates = []

    def compute_dates(self):
        if self.execution_mode and self.delay is not None:
            # Simplified calculation
            self.start_date = self.delay
            self.end_date = self.start_date + self.execution_mode.duration
            self.busy_dates = list(range(self.start_date, self.end_date))

    def __repr__(self):
        return f"Allocation(id={self.id}, job={self.job.id})"
