from datetime import datetime, timedelta
import unittest

from lekin.lekin_struct import Job, Operation, Resource, Route, TimeSlot
from lekin.solver.meta_heuristics.branch_and_bound import BranchAndBoundScheduler

# class BranchAndBoundSchedulerTest(unittest.TestCase):
#     def test_schedule(self):
#         job1 = Job(1, datetime(2023, 1, 10), 2, 1)
#         job2 = Job(2, datetime(2023, 1, 20), 1, 1)
#
#         op1 = Operation(1, timedelta(hours=2), 2, None, [1])
#         op2 = Operation(2, timedelta(hours=3), None, 1, [1])
#
#         route1 = Route(1, [op1, op2])
#         print(route1)
#
#         resource1 = Resource(1, [TimeSlot(datetime(2023, 1, 1), datetime(2023, 1, 3))])
#
#         job_list = [job1, job2]
#         resource_list = [resource1]
#
#         scheduler = BranchAndBoundScheduler(job_list, resource_list)
#         schedule = scheduler.get_schedule()
#         for idx, slot in enumerate(schedule):
#             print(f"Job {idx + 1} will start at {slot.start_time} and end at {slot.end_time}")
