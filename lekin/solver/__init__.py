"""
交付
连续
均衡
"""

from datetime import datetime, timedelta
import heapq
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple, Type, Union

import pandas as pd

from lekin.lekin_struct.operation import Operation


class CTPSolver(object):
    def __init__(self, optimizers=None):
        self.optimizers = optimizers

    def run(self, job_collector, route_list, resource_collector, operation_resource):
        sorted_index = sort_jobs(job_collector.job_list)
        job_list = [job_collector.job_list[i] for i in sorted_index]

        for i, job in enumerate(job_list):
            route_id = job.assigned_route_id
            route = None
            for r in route_list:
                if r.route_id == route_id:
                    route = r
                    break
            if not route:
                print(f"Route with ID '{job.assigned_route_id}' not found for Job ID '{job.job_id}'. Skipping job.")
                continue

            operations_sequence = route.operations_sequence[::-1]  # Reverse the operations in the route
            print([i.operation_id for i in operations_sequence])

            current_end_time = job.demand_date

            for operation in operations_sequence:
                job_id = job.job_id
                operation_id = operation.operation_id

                temp = operation_resource.loc[
                    (operation_resource["产品ID"] == job_id) & (operation_resource["工序ID"] == operation_id)
                ]

                operation.available_resource = [
                    resource_collector.get_resource_by_id(i) for i in temp["资源需求组合ID"].tolist()
                ]
                operation.processing_time = temp["任务加工时长"].tolist()
                operation.quantity = job.quantity

                print(
                    operation.operation_id,
                    operation.available_resource,
                    operation.processing_time,
                    operation.quantity,
                    current_end_time,
                )

                # 对于不同工序依赖进行更新 & calculate the time constraint
                # Calculate earliest and latest start times based on demand time and route constraint
                latest_end_time = current_end_time
                if operation.next_operation_ids is not None:
                    pass
                # get_operation_time_constraint()

                resource, start_time, end_time = find_best_resource_and_timeslot_for_operation(
                    operation, latest_end_time=latest_end_time
                )

    def reschedule_operation(self, operation):
        # TODO: Implement dynamic rescheduling logic here, considering conflicts with other operations,
        # resource availability, and any other relevant constraints.
        pass


def sort_jobs(jobs):
    # Custom sorting function based on priority and continuity
    def custom_sort(job):
        priority_weight = job.priority  # You may adjust the weight based on your requirements
        # continuity_weight = -self.calculate_gap_time(job)
        return priority_weight  # + continuity_weight

    # jobs = sorted(jobs, key=custom_sort, reverse=True)
    return [i[0] for i in sorted(enumerate(jobs), key=lambda x: custom_sort(x[1]), reverse=False)]


def get_operation_time_constraint():
    # calculate the earliest start time and latest end time
    return


def find_best_resource_and_timeslot_for_operation(
    operation: Operation, earliest_start_time=None, latest_end_time=None, allowed_conflict=False
):
    # assign operation
    resource_timeslots_pq: List = []  # Create a priority queue to store the possible resource-time slot pairs
    available_resource = operation.available_resource
    # if operation.required_resource_priority is not None:
    #     required_resource.sort()  # Sort by resource priority

    for i, resource in enumerate(available_resource):
        # start_time = max(operation.prev_operation.end_time, earliest_start_time)
        # end_time = min(start_time + operation.processing_time, latest_end_time)

        resource_all_available_end_time = [slot.end_time for slot in resource.available_timeslots]
        just_in_time_end_time_slot = max([i for i in resource_all_available_end_time if i <= latest_end_time])
        print(latest_end_time, just_in_time_end_time_slot)

        if hasattr(operation.beat_time, "__iter__"):
            working_hours = (operation.beat_time[i] * operation.quantity) / 60

        unoccupied_hours = resource.get_available_time_slots_within_time()
        if unoccupied_hours >= working_hours:
            # assign
            pass
        else:
            pass

        # required processing time and time slot

        just_in_time_slot = find_time_slots(resource, operation, "just_in_time")
        if just_in_time_slot:
            evaluation_score = calculate_evaluation_score(operation, just_in_time_slot, resource)
            heapq.heappush(resource_timeslots_pq, (evaluation_score, resource, just_in_time_slot))

        # If no "just in time" time slot is found, search for available time slots in the past
        if not resource_timeslots_pq:
            past_time_slots = find_time_slots(resource, operation, "history")
            for timeslot in past_time_slots:
                evaluation_score = calculate_evaluation_score(operation, timeslot, resource)
                heapq.heappush(resource_timeslots_pq, (evaluation_score, resource, timeslot))

        # If still no suitable time slot is found, look for available time slots in the future
        # if in future, all the next operation need to be rescheduling forwards
        if not resource_timeslots_pq:
            future_time_slots = find_time_slots(resource, operation, "future")
            for timeslot in future_time_slots:
                evaluation_score = calculate_evaluation_score(operation, timeslot, resource)
                heapq.heappush(resource_timeslots_pq, (evaluation_score, resource, timeslot))

    if resource_timeslots_pq:
        _, chosen_resource, chosen_timeslot = heapq.heappop(resource_timeslots_pq)
        operation.assigned_resource = chosen_resource
        operation.assigned_timeslot = chosen_timeslot
        resource.available_timeslots -= chosen_timeslot
        return True


def find_just_in_time_slots(resource, num_time_slots, duration_hours, job_demand_date):
    available_slots = resource.get_available_time_slots()
    just_in_time_slots = []

    for slot in available_slots:
        slot_end = slot + duration_hours
        if slot_end <= job_demand_date:
            just_in_time_slots.append(slot)
            if len(just_in_time_slots) >= num_time_slots:
                break

    return just_in_time_slots


def find_time_slots(resource, operation, time_slot_type, latest_end_time, working_hours):
    # Find available time slots in the resource for the operation.
    # The time_slot_type can be 'just_in_time', 'history', or 'future'.
    end_time = [slot.end_time for slot in resource.time_slots]
    time_slots = []
    if time_slot_type == "just_in_time":
        # Find a "just in time" time slot where the operation can finish just before the job's demand date.

        resource_all_available_end_time = [slot.end_time for slot in resource.available_timeslots]
        just_in_time_end_time_slot = max([i for i in resource_all_available_end_time if i <= latest_end_time])
        unoccupied_hours = resource.get_available_time_slots_within_time(just_in_time_end_time_slot)
        if unoccupied_hours >= working_hours:
            duration_hours = 0
            for slot in unoccupied_hours[::-1]:
                time_slots.append(slot)
                duration_hours += len(slot.hours)

                if duration_hours >= working_hours:
                    break

    elif time_slot_type == "history":
        # Find available time slots in the past that allow the operation to finish before the demand date.
        past_time_slots = []
        for slot in resource.timeslots:
            if slot.end_time <= end_time:
                past_time_slots.append(slot)
        return past_time_slots
    elif time_slot_type == "future":
        # Find available time slots in the future that allow the operation to finish before the demand date.
        future_time_slots = []
        for slot in resource.timeslots:
            if slot.start_time >= end_time:
                future_time_slots.append(slot)
        return future_time_slots
    else:
        raise ValueError("Invalid time_slot_type. It should be 'just_in_time', 'history', or 'future'.")


def calculate_evaluation_score(self, operation, timeslots, resource):
    # Implement evaluation function here, consider factors like changeover time, priority, lead time, etc.
    # The evaluation function should consider conflicts with other operations and
    # prioritize the best resource and timeslot sequence
    priority_score = operation.priority
    changeover_score = self.calculate_total_changeover_score(operation, timeslots, resource)

    return priority_score + changeover_score


def calculate_conflicts_hours(resource, operation):
    for op in resource.assigned_operation:
        if operation.time_slot.overlaps_with(op.time_slot):
            # Handle conflict: Apply resolution strategy
            # adjust_start_times(operations[i], operations[j])
            pass
    return


def calculate_delay_hours(operation):
    pass


def calculate_total_changeover_score(resource, operation, timeslots):
    # Implement your total changeover calculation
    # calculate the changeover time between the current operation and the previous one in the resource's task sequence

    # Example: A simple total changeover calculation based on processing time of the previous operation
    total_changeover_time = 0
    if resource.assigned_operation:
        previous_operation = resource.task_sequence[-1].operation
        for timeslot in timeslots:
            total_changeover_time += abs(previous_operation.processing_time - operation.processing_time)

    return total_changeover_time


class ConflictResolver:
    def __init__(self, resources):
        self.resources = resources

    def merge_and_resolve(self):
        # Merge backward and forward schedules
        for resource in self.resources:
            resource.merge_schedules()

        # Resolve conflicts
        for resource in self.resources:
            self.resolve_conflicts(resource)

    def resolve_conflicts(self, resource):
        # Find overlapping operations on the same resource at the same time
        overlapping_ops = self.find_overlapping_operations(resource)

        # Resolve conflicts
        for op1, op2 in overlapping_ops:
            # Adjust the start or end time of operations to resolve conflicts
            self.adjust_times_for_conflict(op1, op2)

    def find_overlapping_operations(self, resource):
        overlapping_ops = []
        for time_slot in resource.schedules:
            ops_in_timeslot = resource.schedules[time_slot]
            if len(ops_in_timeslot) > 1:
                # Multiple operations in the same time slot indicate a conflict
                for i in range(len(ops_in_timeslot)):
                    for j in range(i + 1, len(ops_in_timeslot)):
                        overlapping_ops.append((ops_in_timeslot[i], ops_in_timeslot[j]))
        return overlapping_ops

    def adjust_times_for_conflict(self, op1, op2):
        # Implement your logic to adjust the start or end time of operations
        # based on your specific requirements and constraints.
        # You can consider factors like priority, changeovers, lead times, etc.
        # For example, you might want to adjust the end time of op1 or the start time of op2.
        # Check if op2 starts before op1 ends
        if op2.start_time < op1.end_time:
            # Calculate the time difference between op2's start time and op1's end time
            time_difference = op1.end_time - op2.start_time

            # Update op2's start time to be after op1's end time
            op2.start_time += time_difference

            # Adjust the end time of the job if it exceeds the demand date
            if op2.end_time > op2.job.demand_date:
                op2.job.demand_date = op2.end_time

    def resolve_conflicts2(self):
        # Sort operations by their route requirements and processing time
        self.operations.sort(key=lambda op: (op.route.priority, op.processing_time))

        for operation in self.operations:
            # Find a suitable time slot for the operation
            suitable_time_slot = self.find_suitable_time_slot(operation)

            if suitable_time_slot is not None:
                # Assign the operation to the resource and time slot
                operation.resource = suitable_time_slot.resource
                operation.time_slot = suitable_time_slot

                # Update resource's assigned operations
                suitable_time_slot.resource.assign_operation(operation)

    def find_suitable_time_slot(self, operation):
        # Sort available time slots based on priority, earliest start time, and resource availability
        available_time_slots = sorted(
            self.resources,
            key=lambda resource: (
                resource.priority,
                resource.get_earliest_start_time(),
                resource.get_latest_end_time(),
            ),
        )

        for time_slot in available_time_slots:
            # Check if the resource's time slot is compatible with the operation's route
            if time_slot.resource.is_compatible_route(operation.route):
                # Check if there are any conflicts with other operations in the time slot
                if not time_slot.has_conflicts(operation.processing_time):
                    return time_slot

        return None  # No suitable time slot found


# --
#
#         for start_index in range(len(resource.timeslots) - operation.required_time_slots + 1):
#             # Check if consecutive time slots can accommodate the entire operation
#             can_accommodate = True
#             for i in range(operation.required_time_slots):
#                 timeslot = resource.timeslots[start_index + i]
#                 if self.check_timeslot_conflict(resource, timeslot):
#                     can_accommodate = False
#                     break
#
#             if can_accommodate:
#                 end_index = start_index + operation.required_time_slots - 1
#                 evaluation_score = self.calculate_evaluation_score(operation,
#                                                                    resource.timeslots[start_index:end_index + 1],
#                                                                    resource)
#                 heappush(priority_queue, (evaluation_score, resource, resource.timeslots[start_index:end_index + 1]))
#
#         if end_time >= start_time + processing_time:
#             delay_time = max(0, operation.job.demand_date - end_time)
#             changeover_time = self.calculate_changeover_time(last_operation, resource)
#             priority_score = delay_time + changeover_time + resource.priority
#             heapq.heappush(resource_timeslots, (priority_score, resource, start_time, end_time))
#
#     while resource_timeslots:
#         _, resource, start_time, end_time = heapq.heappop(resource_timeslots)
#
#         # Create a temporary timeslot for the operation
#         temp_timeslot = Timeslot(start_time, end_time)
#
#         # Check if the time slot overlaps with any of the previous task's timeslots
#         if not self.check_timeslot_conflict(resource, temp_timeslot):
#             # Assign the operation to the current resource and timeslot
#             operation.assigned_resource = resource
#             operation.assigned_timeslot = temp_timeslot
#     return
