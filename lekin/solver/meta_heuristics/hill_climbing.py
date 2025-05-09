"""Hill climbing"""

import random


class HillClimbingScheduler:
    def __init__(self, job_collector):
        self.job_collector = job_collector

    def schedule(self, max_iterations=1000):
        current_solution = self.random_solution()
        current_score = self.evaluate_solution(current_solution)

        for _ in range(max_iterations):
            neighbors = self.get_neighbors(current_solution)
            if not neighbors:
                break

            next_solution = max(neighbors, key=lambda neighbor: self.evaluate_solution(neighbor))
            next_score = self.evaluate_solution(next_solution)

            if next_score <= current_score:
                current_solution = next_solution
                current_score = next_score
            else:
                break

        return current_solution

    def random_solution(self):
        return {
            operation: random.randint(0, operation.get_latest_start_time())
            for job in self.job_collector.jobs
            for operation in job.route.operations
        }

    def get_neighbors(self, solution):
        neighbors = []
        for operation, start_time in solution.items():
            for t in range(start_time - 1, operation.get_latest_start_time() + 1):
                neighbor = solution.copy()
                neighbor[operation] = t
                neighbors.append(neighbor)
        return neighbors

    def evaluate_solution(self, solution):
        end_times = {}
        for job in self.job_collector.jobs:
            for operation in job.route.operations:
                if operation in solution:
                    start_time = solution[operation]
                else:
                    start_time = operation.get_latest_start_time()

                end_time = start_time + operation.processing_time
                if operation.id not in end_times or end_time > end_times[operation.id]:
                    end_times[operation.id] = end_time

        makespan = max(end_times.values())
        return makespan
