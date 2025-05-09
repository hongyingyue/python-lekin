"""Earliest Possible Start Time
Forward scheduler
正排"""

import logging
import math

from lekin.solver.construction_heuristics.base import BaseScheduler


class ForwardScheduler(BaseScheduler):
    def __init__(self, job_collector, resource_collector, route_collector=None, **kwargs):
        super().__init__(job_collector, resource_collector, **kwargs)
        self.job_collector = job_collector
        self.resource_collector = resource_collector
        self.route_collector = route_collector

        for key, value in kwargs.items():
            setattr(self, key, value)

    def run(self):
        for i, job in enumerate(self.job_collector.job_list):
            self.scheduling_job(job, self.resource_collector, self.route_collector)
        logging.info("First Scheduling Done")

        for i, job in enumerate(self.job_collector.job_list):
            self.rescheduling_job_to_resolve_conflict(job)
        logging.info("ReScheduling Done")
        return

    def scheduling_job(self, job, resource_collector, route_collector):
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

        op_earliest_start = 0
        for operation in job.operations:
            logging.info(f"\tAssign Operation {operation.operation_id} of Job {job.job_id}")
            chosen_resource, chosen_timeslot_hour = self.find_best_resource_and_timeslot_for_operation(
                operation, op_earliest_start
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

                op_earliest_start = chosen_timeslot_hour[-1] + 1
        return

    def find_best_resource_and_timeslot_for_operation(self, operation, op_earliest_start, **kwargs):
        available_resource = operation.available_resource

        earliest_index = 0
        resource_earliest_time = float("inf")
        for i, resource in enumerate(available_resource):
            resource_time = resource.get_earliest_available_time(duration=operation.processing_time)

            if resource_time < resource_earliest_time:
                earliest_index = i
                resource_earliest_time = resource_time

        chosen_resource = available_resource[earliest_index]
        earliest_time = int(max(op_earliest_start, resource_earliest_time))
        chosen_hours = list(range(earliest_time, earliest_time + math.ceil(operation.processing_time)))
        return chosen_resource, chosen_hours

    def rescheduling_job_to_resolve_conflict(self, job):
        op_earliest_start = 0
        for operation in job.operations:
            logging.info(f"Rescheduling {job.job_id}/ {operation.operation_id}")
            assigned_resource = operation.assigned_resource
            if operation.assigned_hours[0] < op_earliest_start:
                delta = op_earliest_start - operation.assigned_hours[0]
                operation.assigned_hours = [i + delta for i in operation.assigned_hours]

            pivot_assigned_hours = operation.assigned_hours
            op_earliest_start = pivot_assigned_hours[-1] + 1

            ops_in_same_resource = assigned_resource.assigned_operations
            ops_in_same_resource.sort(key=lambda x: x.assigned_hours[0], reverse=False)
            logging.info([i.parent_job_id for i in ops_in_same_resource])
            for op in ops_in_same_resource:
                if op != operation:
                    op_start = op.assigned_hours[0]
                    if set(pivot_assigned_hours).intersection(set(op.assigned_hours)):
                        logging.info(
                            f"\tRescheduling {job.job_id}/ {op.operation_id} in {assigned_resource.resource_id}"
                        )
                        op.assigned_hours = [i + pivot_assigned_hours[-1] - op_start + 1 for i in op.assigned_hours]
        return
