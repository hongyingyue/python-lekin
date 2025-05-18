from datetime import datetime, timedelta
from itertools import permutations

from lekin.lekin_struct import TimeSlot


class BranchAndBoundScheduler:
    def __init__(self, job_list, resource_list):
        self.job_list = job_list
        self.resource_list = resource_list
        self.best_schedule = None
        self.best_cost = float("inf")

    def find_available_time_slots(self, operation, resource, current_time):
        # Implement the logic to find available time slots for a given operation and resource
        available_time_slots = []
        for slot in resource.available_time_slots:
            if slot.start_time >= current_time + operation.processing_time:
                available_time_slots.append(slot)
        return available_time_slots

    def assign_operation(self, job, operation, resource, start_time):
        # Implement the logic to assign an operation to a resource at a specific start time
        end_time = start_time + operation.processing_time
        resource.available_time_slots.append(TimeSlot(end_time, float("inf")))
        return end_time

    def calculate_cost(self, schedule):
        # Implement the logic to calculate the cost of the current schedule
        # For example, you can calculate makespan or any other relevant metric
        makespan = max(slot.end_time for slot in schedule)
        return makespan

    def branch_and_bound(self, current_job_idx, current_time, schedule):
        # Implement the Branch and Bound algorithm for scheduling
        if current_job_idx == len(self.job_list):
            cost = self.calculate_cost(schedule)
            if cost < self.best_cost:
                self.best_cost = cost
                self.best_schedule = schedule.copy()
            return

        job = self.job_list[current_job_idx]
        route = self.resource_list[job.assigned_route_id]

        for resource_id in route.operations[0].resource_ids:
            resource = self.resource_list[resource_id]
            time_slots = self.find_available_time_slots(route.operations[0], resource, current_time)
            for slot in time_slots:
                new_schedule = schedule + [slot]
                new_time = self.assign_operation(job, route.operations[0], resource, slot.start_time)
                self.branch_and_bound(current_job_idx + 1, new_time, new_schedule)

    def get_schedule(self):
        # Implement the main function to get the final schedule using Branch and Bound
        self.branch_and_bound(0, datetime(2023, 1, 1), [])
        return self.best_schedule
