"""Critical path"""

import copy
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple, Type, Union


class CriticalPathScheduler:
    def __init__(self, job_collector):
        self.job_collector = job_collector

    def schedule(self):
        # Generate the forward and backward pass times
        forward_pass_times = self.forward_pass()
        backward_pass_times = self.backward_pass()

        # Find the critical path
        critical_path = self.find_critical_path(forward_pass_times, backward_pass_times)

        # Assign start times for each operation in the critical path
        critical_path_schedule = {}
        current_time = 0
        for job_id, operation_id in critical_path:
            operation = self.job_collector.get_operation_by_id(job_id, operation_id)
            critical_path_schedule[operation] = current_time
            current_time += operation.processing_time

        return critical_path_schedule

    def forward_pass(self):
        forward_pass_times: Dict[str, Dict[str, float]] = {}
        for job in self.job_collector.jobs:
            forward_pass_times[job.id] = {}
            for operation in job.route.operations:
                if operation.id == 0:
                    forward_pass_times[job.id][operation.id] = 0
                else:
                    predecessors = operation.get_predecessors()
                    max_predecessor_time = max(
                        [forward_pass_times[job.id][pred.id] + pred.processing_time for pred in predecessors]
                    )
                    forward_pass_times[job.id][operation.id] = max_predecessor_time

        return forward_pass_times

    def backward_pass(self):
        backward_pass_times: Dict[str, Dict[str, float]] = {}
        for job in self.job_collector.jobs:
            backward_pass_times[job.id] = {}
            for operation in reversed(job.route.operations):
                if operation.id == len(job.route.operations) - 1:
                    backward_pass_times[job.id][operation.id] = operation.processing_time
                else:
                    successors = operation.get_successors()
                    min_successor_time = min(
                        [backward_pass_times[job.id][succ.id] + succ.processing_time for succ in successors]
                    )
                    backward_pass_times[job.id][operation.id] = min_successor_time

        return backward_pass_times

    def find_critical_path(self, forward_pass_times, backward_pass_times):
        critical_path = []
        for job in self.job_collector.jobs:
            for operation in job.route.operations:
                start_time = forward_pass_times[job.id][operation.id]
                end_time = backward_pass_times[job.id][operation.id]
                if start_time + operation.processing_time == end_time:
                    critical_path.append((job.id, operation.id))

        return critical_path
