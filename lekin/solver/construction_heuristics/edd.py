"""Earliest Due Date"""

import logging

from lekin.solver.construction_heuristics.base import BaseScheduler


class EDDScheduler(object):
    def __init__(self, jobs, routes):
        self.jobs = jobs
        self.routes = routes

    def schedule_job(self, job):
        # Schedule the operations of a job using EDD method
        current_time = 0
        for operation in job.route.operations:
            operation.start_time = max(current_time, operation.available_time)
            operation.end_time = operation.start_time + operation.processing_time
            current_time = operation.end_time

    def run(self):
        for job in self.jobs:
            self.schedule_job(job)


class MS(object):
    """Variation of EDD"""

    def __init__(self):
        pass
