"""Apparent Tardiness Cost"""

import logging

from lekin.solver.construction_heuristics.base import BaseScheduler


class ATCScheduler(object):
    def __init__(self, jobs, routes):
        self.jobs = jobs
        self.routes = routes

    def calculate_tardiness_cost(self, operation):
        # Calculate the tardiness cost for an operation based on its finish time and due date
        if operation.end_time > operation.due_date:
            return operation.end_time - operation.due_date
        else:
            return 0

    def schedule_job(self, job):
        # Schedule the operations of a job using ATC method
        for operation in job.route.operations:
            operation.start_time = max(operation.available_time, operation.earliest_start_time)
            operation.end_time = operation.start_time + operation.processing_time

        # Sort the operations by their tardiness cost in descending order
        sorted_operations = sorted(job.route.operations, key=self.calculate_tardiness_cost, reverse=True)

        # Reschedule the operations based on their tardiness cost
        current_time = 0
        for operation in sorted_operations:
            operation.start_time = max(current_time, operation.earliest_start_time)
            operation.end_time = operation.start_time + operation.processing_time
            current_time = operation.end_time

    def run(self):
        for job in self.jobs:
            self.schedule_job(job)
