"""
Resource/Machine Struct
"""

import math
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple, Type, Union

import numpy as np
import pandas as pd

from lekin.lekin_struct.timeslot import TimeSlot
from lekin.objective import ResourceObjective


class Resource:
    def __init__(self, resource_id, resource_name=None, max_tasks=1, virtual_calender: bool = True, **kwargs):
        self.resource_id = resource_id
        self.resource_name = resource_name
        self.max_tasks = max_tasks  # maximum task can be done in same time, capacity
        self.tasks = {time_slot: None for time_slot in range(1, max_tasks + 1)}
        self._available_timeslots = []
        self._available_hours = []

        self.assigned_operations = []
        self.assigned_time_slots = []
        self.assigned_hours = []
        self.pending_list = []  # 临时缓冲区
        self.changeover_number = None  # number of times
        self.changeover_time = None  # total time costs

        for key, value in kwargs.items():
            setattr(self, key, value)

    def add_timeslot(self, start_time, end_time):
        self._available_timeslots.append(TimeSlot(start_time, end_time))
        # self._available_hours += TimeSlot(start_time, end_time).hours

    def add_available_hours(self, hours):
        self._available_hours = hours

    @property
    def available_hours(self):
        return self._available_hours

    @available_hours.setter
    def available_hours(self, available_hours):
        self._available_hours = available_hours

    def init_job_op_from_op(self):
        """op-> job_op"""
        pass

    def init_material_op_from_group_op(self):
        """group_op-> material_op"""
        pass

    def update_op_from_material_op(self):
        """material_op -> op"""
        pass

    def get_available_timeslot_for_op(self, start=None, end=None, periods=None, freq="1H", forward=True):
        self.update_continuous_empty_hours()
        select_hours = [i for i in self.available_hours if i <= end]

        assert len(self.available_hours) == len(self.continuous_empty_hours)
        front_available = self.continuous_empty_hours[: len(select_hours)]

        chosen_hours_index = self.find_last_index_larger(periods, front_available)

        if not chosen_hours_index:
            back_available = self.continuous_empty_hours[len(select_hours) :]
            chosen_hours_index = self.find_first_index_larger(periods, back_available)

        if chosen_hours_index:
            chosen_hours = self.available_hours[int(chosen_hours_index - periods) : chosen_hours_index]
            return chosen_hours
        else:
            return []

    def get_earliest_available_time(self, duration=None, start=None):
        if len(self.available_hours) > len(self.assigned_hours):
            return min(set(self.available_hours).difference(set(self.assigned_hours)))
        else:
            return None

    def get_latest_available_time(self, duration=None, end=None):
        self.update_continuous_empty_hours()
        return max([i + 1 for (i, v) in enumerate(self.continuous_empty_hours[:end]) if v >= duration])

    def update_continuous_empty_hours(self):
        if len(self.available_hours) != len(self._available_timeslots):
            pass
        if len(self.assigned_hours) != len(self.assigned_time_slots):
            pass

        # for hours_list in self.available_hours:
        empty_hours = []
        continuous_hours = 0

        for hour in self.available_hours:
            if hour in self.assigned_hours:  # Hour is not available
                continuous_hours = 0
            else:
                continuous_hours += 1
            empty_hours.append(continuous_hours)
        self.continuous_empty_hours = empty_hours

    def find_first_index_larger(self, input_value, lists):
        for j, value in enumerate(lists):
            if value > input_value:
                return j
        return None

    def find_last_index_larger(self, input_value, lists):
        lists = lists[::-1]
        for j, value in enumerate(lists):
            if value > input_value:
                return len(lists) - j
        return None

    def get_available_time_slots_within_time(self, start=None, end=None, periods=None, freq="1H", forward=True):
        available_hours = []

        # check_periods = pd.date_range(start=start, end=end, periods=periods, freq=freq)
        # if not forward:
        #     check_periods = check_periods[::-1]
        # occupied_periods = [i.hours for i in self.assigned_time_slot]
        # for period in check_periods:
        #     if period not in occupied_periods:
        #         available_hours.append(period)
        #     else:  # considering the continuous assignment
        #         break

        # all_available_end_time = [slot.end_time for slot in self.available_timeslots]
        # just_in_time_end_time_slot = max([i for i in all_available_end_time if i <= end])
        if forward:
            selected_time_slot = [i for i in self.available_timeslots if i.start_time >= start]
        else:
            selected_time_slot = [i for i in self.available_timeslots if i.end_time <= end][::-1]

        # print(just_in_time_end_time_slot)
        # print([i.start_time for i in self.available_timeslots])
        # print([i.end_time for i in self.available_timeslots])
        # print(self.available_timeslots[0].hours)

        left_periods = periods

        for time_slot in selected_time_slot:
            if left_periods <= 0:
                break

            if start and time_slot.start_time < start:
                continue

            if end and time_slot.start_time >= end:
                break

            # if forward:
            #     current_time = max(start, time_slot.start_time)
            # else:
            #     current_time = min(end, time_slot.end_time)

            if time_slot in self.assigned_time_slot:
                break

            if time_slot.duration_of_hours < left_periods:
                available_hours += time_slot.hours
                left_periods -= time_slot.duration_of_hours

            else:
                available_hours += time_slot.hours[-math.ceil(left_periods) :]
                break
            #
            # print(left_periods, available_hours)

            # for current_time in range(max(start, time_slot.start_time),
            #                           min(end, time_slot.end_time - period) + 1):
            #     if all(self.is_available(current_time + offset, current_time +offset+1) for offset in range(periods)):
            #         available_hours.append(current_time)

        return available_hours

    def is_available(self, start_time, end_time):
        for assigned_time_slot in self.assigned_time_slots:
            if not (end_time <= assigned_time_slot.start_time or start_time >= assigned_time_slot.end_time):
                return False
        return True

    def get_unoccupied_time_slots_within_time(self):
        unoccupied_slots = []
        prev_end_time = None
        for time_slot in self.time_slots:
            if not time_slot.is_occupied():
                if prev_end_time:
                    # Check if there is a gap between unoccupied time slots
                    if time_slot.start_time > prev_end_time:
                        unoccupied_slots.append(TimeSlot(prev_end_time, time_slot.start_time))
                unoccupied_slots.append(time_slot)
                prev_end_time = time_slot.end_time
        return unoccupied_slots

    def merge_schedules(self):
        # Sort timeslots based on start time
        self.timeslots.sort(key=lambda x: x.start_time)

        merged_slots = []
        current_slot = None

        for slot in self.timeslots:
            if not current_slot:
                current_slot = slot
            else:
                # If the current slot and the next slot overlap, merge them
                if current_slot.end_time >= slot.start_time:
                    current_slot.end_time = max(current_slot.end_time, slot.end_time)
                else:
                    merged_slots.append(current_slot)
                    current_slot = slot

        if current_slot:
            merged_slots.append(current_slot)

        self.timeslots = merged_slots

    def __hash__(self):
        return hash(str(self))

    def __str__(self):
        return f"{self.resource_id}"

    def __eq__(self, other):
        return self.resource_id == other.resource_id

    def __lt__(self, other):
        return self.resource_id < other.resource_id

    def __repr__(self):
        return f"Resource(id={self.id}, name={self.name})"


class ResourceCollector:
    def __init__(self):
        self.resources = {}
        self.index = -1

    def __iter__(self):
        return self

    def __next__(self):
        self.index += 1
        if self.index < len(self.resources):
            return list(self.resources.values())[self.index]
        else:
            raise StopIteration("Stop")

    def add_resource_dict(self, resource: Resource):
        self.resources.update({resource.resource_id: resource})

    def get_resource_by_id(self, resource_id):
        return self.resources.get(resource_id)

    def get_all_resources(self):
        return list(self.resources.values())

    def get_unoccupied_time_slots(self):
        unoccupied_slots = []
        for resource in self.get_all_resources():
            unoccupied_slots.extend(resource.get_unoccupied_time_slots())
        return unoccupied_slots
