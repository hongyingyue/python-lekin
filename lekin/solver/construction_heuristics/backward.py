"""Latest Possible Start Time
Backward scheduler
倒排"""

import logging
import math

from lekin.lekin_struct.job import Job, JobCollector
from lekin.lekin_struct.operation import Operation
from lekin.lekin_struct.resource import ResourceCollector
from lekin.lekin_struct.route import RouteCollector
from lekin.lekin_struct.timeslot import TimeSlot
from lekin.solver.construction_heuristics.base import BaseScheduler


class BackwardScheduler(object):
    def __init__(
        self,
        job_collector: JobCollector,
        resource_collector: ResourceCollector,
        route_collector: RouteCollector = None,
        **kwargs,
    ) -> None:
        self.job_collector = job_collector
        self.resource_collector = resource_collector
        self.route_collector = route_collector

        for key, value in kwargs.items():
            setattr(self, key, value)

    def run(self) -> None:
        for i, job in enumerate(self.job_collector.job_list):
            self.scheduling_job(job, self.resource_collector, self.route_collector)
        logging.info("First Scheduling Done")
        return

    def scheduling_job(self, job: Job, resource_collector, route_collector: RouteCollector) -> None:
        logging.info(f"\nAssign Job {job.job_id}")

        if route_collector is not None:
            route_id = job.assigned_route_id
            route = None
            for r in route_collector:
                if r.route_id == route_id:
                    route = r
                    break
            if not route:
                print(f"Route with ID '{job.assigned_route_id}' not found for Job ID '{job.job_id}'. Skipping job.")

            job.operations = route.operations_sequence

        op_earliest_start = 0  # forward constraint
        op_latest_end = 150  # backward constraint
        for operation in job.operations[::-1]:  # inverse
            logging.info(f"\tAssign Operation {operation.operation_id} of Job {job.job_id}")
            chosen_resource, chosen_timeslot_hour = self.find_best_resource_and_timeslot_for_operation(
                operation, op_latest_end, op_earliest_start
            )

            if chosen_resource and chosen_timeslot_hour:
                logging.info(
                    f"\tOperation {operation.operation_id} assigned in: resource"
                    f" {chosen_resource.resource_id}, {min(chosen_timeslot_hour)} -"
                    f" {max(chosen_timeslot_hour)}"
                )

                # assign
                operation.assigned_resource = chosen_resource
                operation.assigned_hours = chosen_timeslot_hour
                chosen_resource.assigned_operations.append(operation)
                chosen_resource.assigned_hours += chosen_timeslot_hour

                # op_earliest_start = chosen_timeslot_hour[-1] + 1
                op_latest_end = chosen_timeslot_hour[0] - 1
        return

    def find_best_resource_and_timeslot_for_operation(
        self, operation: Operation, op_latest_end=None, op_earliest_start=None, **kwargs
    ):
        available_resource = operation.available_resource

        latest_index = float("inf")
        resource_latest_time = 0
        for i, resource in enumerate(available_resource):
            resource_time = resource.get_latest_available_time(duration=operation.processing_time, end=op_latest_end)

            if resource_time > resource_latest_time:
                latest_index = i
                resource_latest_time = resource_time

        chosen_resource = available_resource[latest_index]
        latest_time = int(min(op_latest_end, resource_latest_time))
        chosen_hours = list(range(latest_time - math.ceil(operation.processing_time), latest_time + 0))
        return chosen_resource, chosen_hours

    def assign_operation(self, operation: Operation, start_time, end_time, resources):
        timeslot = TimeSlot(start_time, end_time)
        self.timeslots.append(timeslot)
        for resource in resources:
            # Add timeslot to resource's schedule
            resource.schedule.append(timeslot)
        # Link operation to scheduled timeslot
        operation.scheduled_timeslot = timeslot

    def select_resources(self, job: Job, operation: Operation):
        available_slots = self.find_available_timeslots(job, operation)

        selected_resources = []
        for slot in available_slots:
            resources = slot.available_resources()
            resource = self.optimize_resource_selection(resources, operation)
            selected_resources.append((slot, resource))
        return selected_resources

    def find_available_timeslots(self, job, operation):
        # Search timeslots and filter based on:
        # - operation duration
        # - predecessor timeslots
        # - resource requirements

        slots = []
        # for ts in job.schedule.timeslots:
        #     if ts.end - ts.start >= operation.duration:
        #         if all(pred in job.predecessors(ts)):
        #             if ts.meets_resource_needs(operation):
        #                 slots.append(ts)
        return slots

    def optimize_resource_selection(self, resources, operation):
        # Score and prioritize resources based on:
        # - Capacity
        # - Changeover time
        # - Utilization

        scored = []
        for resource in resources:
            score = 0
            if resource.capacity >= operation.required_capacity:
                score += 1
            if resource.type in operation.preferred_resources:
                score += 1
            # Prioritize resources with less adjacent timeslots
            score -= len(resource.adjacent_timeslots(operation))
            scored.append((score, resource))
        best = max(scored, key=lambda x: x[0])
        return best[1]
