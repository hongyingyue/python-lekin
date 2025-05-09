"""Critical ratio rule"""

import logging

from lekin.solver.construction_heuristics.base import BaseScheduler


class CRScheduler(object):
    def __init__(self, jobs, routes):
        self.jobs = jobs
        self.routes = routes

    def calculate_critical_ratio(self, operation):
        time_remaining = operation.job.due_date - operation.start_time
        return time_remaining / operation.processing_time

    def schedule_job(self, job):
        # Schedule the operations of a job using CR method
        current_time = 0
        for operation in job.route.operations:
            operation.start_time = max(current_time, operation.available_time)
            operation.end_time = operation.start_time + operation.processing_time
            current_time = operation.end_time

        # Sort the operations based on critical ratio
        job.route.operations.sort(key=self.calculate_critical_ratio, reverse=True)

    def run(self):
        for job in self.jobs:
            self.schedule_job(job)
