"""Shifting bottle neck meta_heuristics"""

import copy


class ShiftingBottleneckScheduler:
    def __init__(self, job_collector):
        self.job_collector = job_collector

    def schedule(self):
        best_solution = self.generate_initial_solution()
        best_cost = self.calculate_cost(best_solution)

        for _ in range(1000):  # Number of iterations
            current_solution = copy.deepcopy(best_solution)
            bottleneck_job, bottleneck_op = self.find_bottleneck_operation(current_solution)

            # Move bottleneck operation to different time slots
            for time_slot in range(self.job_collector.max_time):
                current_solution[bottleneck_job.id][bottleneck_op.id] = time_slot
                current_cost = self.calculate_cost(current_solution)

                if current_cost < best_cost:
                    best_solution = current_solution
                    best_cost = current_cost

        return best_solution

    def generate_initial_solution(self):
        # Randomly assign operations to time slots
        solution = {}
        for job in self.job_collector.jobs:
            solution[job.id] = {op.id: 0 for op in job.route.operations}
        return solution

    def find_bottleneck_operation(self, solution):
        # Find the operation with the longest processing time in the schedule
        max_processing_time = 0
        bottleneck_job = None
        bottleneck_op = None

        for job in self.job_collector.jobs:
            for operation in job.route.operations:
                processing_time = operation.processing_time
                start_time = solution[job.id][operation.id]
                end_time = start_time + processing_time

                if end_time > max_processing_time:
                    max_processing_time = end_time
                    bottleneck_job = job
                    bottleneck_op = operation

        return bottleneck_job, bottleneck_op

    def calculate_cost(self, solution):
        # Calculate the makespan of the schedule
        max_end_time = 0
        for job in self.job_collector.jobs:
            end_time = max(
                [solution[job.id][operation.id] + operation.processing_time for operation in job.route.operations]
            )
            max_end_time = max(max_end_time, end_time)
        return max_end_time
