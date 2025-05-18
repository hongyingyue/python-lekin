"""Shortest Processing Time"""

from collections import OrderedDict
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from lekin.solver.construction_heuristics.base import BaseScheduler


class SPTScheduler(object):
    def __init__(self):
        self.time = {}  # global时间队列
        self.waiting_operations = {}  # 记录每个机器的任务等待队列
        self.jobs_list_to_export = []

    def setup(self, job_list: List, machine_list: List):
        for machine in machine_list:
            # init for machine start time
            self.current_time_on_machines[machine.name] = 0

            # init for waiting list of machines
            self.waiting_operations[machine.name] = 0
            for job in job_list:
                if job.operation_id == 1 and machine.name in job.machine:
                    if len(job.machine) == 1:
                        self.waiting_operations[machine.name].append(job)

            self.waiting_operations[machine.name].sort(key=lambda j: j.duration)
        return

    def solve(self, job_list: List, machine_list: List):
        self.setup(job_list, machine_list)

        self.time[0] = self.waiting_operations

        for key_mach, operations in self.waiting_operations.items():
            # for each waiting task in front of machine, set time to 0
            if len(operations):
                operations[0].start_time = 0
                operations[0].completed = True
                operations[0].assigned_machine = key_mach

                self.jobs_list_to_export.append(operations[0])
                self.current_time_on_machines[key_mach] = operations[0].get_end_time()
                self.time[self.current_time_on_machines[key_mach]] = {}

        while len(self.jobs_list_to_export) != len(job_list):
            for t, operations in self.time.items():
                operations = self.get_waiting_operations(
                    job_list, float(t), machine_list, self.current_time_on_machines
                )

                for key_mach, tasks in operations.items():
                    if len(tasks):
                        if float(t) < self.current_time_on_machines[key_mach]:
                            continue

                        tasks[0].start_time = float(t)
                        tasks[0].completed = True
                        tasks[0].assigned_machine = key_mach

                        self.jobs_list_to_export.append(tasks[0])
                        self.current_time_on_machines[key_mach] = tasks[0].get_end_time()
                        self.time[self.current_time_on_machines[key_mach]] = {}

                del self.time[t]
                break
            self.time = OrderedDict(self.time)
        return self.jobs_list_to_export

    def get_waiting_operations(self, job_list, time, machine_list, current_time_on_machines):
        incoming_operations = {}

        for mach in machine_list:
            assigned_jobs_for_machine = []
            for job in job_list:
                if job.completed is False and mach.name in job.machine:
                    if len(job.machine) == 1:
                        assigned_jobs_for_machine.append(job)

            incoming_operations[mach.name] = []
            for j in assigned_jobs_for_machine:
                if j.id_operation == 1:
                    incoming_operations[mach.name].append(j)
                else:
                    previous_task = [
                        job
                        for job in job_list
                        if job.route_id == j.route_id
                        and job.id_operation == (j.id_operation - 1)
                        and job.end_time <= time
                    ]
                    if len(previous_task):
                        if previous_task[0].completed:
                            incoming_operations[mach.name].append(j)

            incoming_operations[mach.name].sort(key=lambda j: j.duration)
        return incoming_operations

    def run(self):
        return
