"""L"""

import logging
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from lekin.solver.construction_heuristics.base import BaseScheduler


class LSTScheduler(object):
    def __init__(self, jobs, routes):
        self.jobs = jobs
        self.routes = routes

    def calculate_slack_time(self, operation, current_time):
        # Calculate the slack time for an operation based on its due date and current time
        return max(0, operation.due_date - current_time)

    def select_next_operation(self, available_operations, current_time):
        # Select the operation with the longest slack time from the available operations
        selected_operation = None
        max_slack_time = float("-inf")

        for operation in available_operations:
            slack_time = self.calculate_slack_time(operation, current_time)
            if slack_time > max_slack_time:
                max_slack_time = slack_time
                selected_operation = operation

        return selected_operation

    def schedule_job(self, job, start_time):
        # Schedule the operations of a job based on LST
        current_time = start_time

        for operation in job.route.operations:
            slack_time = self.calculate_slack_time(operation, current_time)
            print(slack_time)
            operation.start_time = current_time
            operation.end_time = current_time + operation.processing_time
            current_time += operation.processing_time

        job.completion_time = current_time

    def run(self):
        for job in self.jobs:
            self.schedule_job(job, 0)
