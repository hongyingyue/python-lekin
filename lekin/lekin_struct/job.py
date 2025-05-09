"""
Struct Job/订单作业
    - a job could finish one product while finished
    - job/mo/operation/activity
"""

from datetime import datetime
import random
from typing import Any, Callable, Dict, List, Optional, Tuple

from lekin.lekin_struct.operation import Operation

random.seed(315)


class Job(object):
    def __init__(
        self,
        job_id: str,
        job_name: Optional[str] = None,
        priority: int = None,
        quantity: int = None,
        demand_date: datetime = None,
        job_type: str = None,
        earliest_start_time=None,
        assigned_route_id=None,
        assigned_bom_id=None,
        **kwargs: Dict,
    ) -> None:
        self.job_id: str = job_id
        self.job_name = job_name
        self.priority: int = priority
        self.demand_date: datetime = demand_date
        self.quantity: int = quantity
        self.job_type: str = job_type
        self.earliest_start_time: datetime = earliest_start_time  # Material constraint
        # cached scheduling result until the whole job is finished
        self.cached_scheduling: dict = {}
        self.assigned_route_id: str = assigned_route_id  # Route object assigned to this job
        self.assigned_bom_id: str = assigned_bom_id
        self.current_operation_index: int = 0  # Record the current processing operation
        self._operations_sequence: List[Operation] = []  # List of Operation objects for this job

        for key, value in kwargs.items():
            setattr(self, key, value)

    def assign_route(self, route_id):
        self.assigned_route_id = route_id

    @property
    def operations(self):
        return self._operations_sequence

    def ger_next_operation(self):
        if self.current_operation_index < len(self._operations_sequence):
            return self._operations_sequence[self.current_operation_index]
        else:
            return None

    def assign_cached_scheduling(self):
        """assign all cached scheduling officially while all ops are fine"""
        pass

    def clear_cached_scheduling(self, all, start, dir):
        """clear the cached scheduling result"""
        pass

    @operations.setter
    def operations(self, operations_sequence):
        self._operations_sequence = operations_sequence

    def __eq__(self, other):
        return

    def __hash__(self):
        return

    def __str__(self):
        return f"{self.job_id}"

    def __repr__(self):
        return f"Project(id={self.id}, name={self.name})"


class JobCollector:
    def __init__(self):
        self.job_list = []
        self.color_dict = dict()  # List to store colors for job
        self.index = -1

    def __iter__(self):
        return self

    def __next__(self):
        self.index += 1
        if self.index < len(self.job_list):
            return self.job_list[self.index]
        else:
            raise StopIteration("Stop")

    def add_job(self, job: Job) -> None:
        self.job_list.append(job)

    def get_job_by_id(self, job_id: str):
        for job in self.job_list:
            if job.job_id == job_id:
                return job
        return None

    def sort_jobs(self, jobs):
        # Custom sorting function based on priority and continuity
        def custom_sort(job):
            priority_weight = (job.priority, job.demand_date)
            # continuity_weight = -self.calculate_gap_time(job)
            return priority_weight  # + continuity_weight

        # jobs = sorted(jobs, key=custom_sort, reverse=True)
        return [i[0] for i in sorted(enumerate(jobs), key=lambda x: custom_sort(x[1]), reverse=False)]

    def get_schedule(self):
        schedule = {}

        for resource in self.resource_list:
            scheduled_operations = []
            for operation in self.operation_list:
                if operation.resource == resource:
                    scheduled_operations.append({"operation_id": operation.id, "start_time": operation.start_time})

            if scheduled_operations:
                schedule[resource.id] = scheduled_operations

        return schedule

    def generate_color_list_for_jobs(self, pastel_factor=0.5):
        for job in self.job_list:
            max_distance = None
            best_color = None
            for i in range(0, 100):
                color = [
                    (x + pastel_factor) / (1.0 + pastel_factor) for x in [random.uniform(0, 1.0) for i in [1, 2, 3]]
                ]
                if color not in self.color_dict.values():
                    best_color = color
                    break
                else:
                    best_distance = min([self.color_distance(color, c) for c in self.color_dict.values()])
                    if not max_distance or best_distance > max_distance:
                        max_distance = best_distance
                        best_color = color
            self.color_dict.update({job.job_id: best_color})
        return self.color_dict

    @staticmethod
    def color_distance(c1, c2):
        return sum([abs(x[0] - x[1]) for x in zip(c1, c2)])
