"""
Local search
https://towardsdatascience.com/optimization-techniques-tabu-search-36f197ef8e25
https://www.optaplanner.org/docs/optaplanner/latest/local-search/local-search.html
"""

from collections import deque
import math
import random
from typing import TYPE_CHECKING, Any, Callable, List, Optional, Tuple

# if TYPE_CHECKING:
#     from


def evaluate(solution):
    # Example evaluation function (e.g., sum of elements)
    return sum(solution)


def neighborhood_function(solution):
    # Example neighborhood generation (e.g., swap two elements)
    neighbors = []
    for i in range(len(solution)):
        for j in range(i + 1, len(solution)):
            neighbor = solution[:]
            neighbor[i], neighbor[j] = neighbor[j], neighbor[i]
            neighbors.append(neighbor)
    return neighbors


class Step:
    def __init__(self, description: str, change: Any, affected_elements: Optional[List[Any]] = None):
        self.description = description
        self.change = change
        self.affected_elements = affected_elements if affected_elements else []

    def apply(self, solution):
        """
        Apply this step's change to the given solution.

        :param solution: The current solution to which the step should be applied.
        :return: The new solution after applying this step.
        """
        job = self.change["job"]
        from_slot = self.change["from_slot"]
        to_slot = self.change["to_slot"]

        # Remove the job from its current slot
        if job in solution.job_to_slot and solution.job_to_slot[job] == from_slot:
            solution.remove_job_from_slot(job)

        # Assign the job to the new slot
        solution.assign_job_to_slot(job, to_slot)
        return solution

    def undo(self, solution):
        """
        Undo the change applied by this step.

        :param solution: The solution to revert the change.
        :return: The solution after reverting the step.
        """
        job = self.change["job"]
        from_slot = self.change["from_slot"]
        to_slot = self.change["to_slot"]

        # Remove the job from the new slot
        if job in solution.job_to_slot and solution.job_to_slot[job] == to_slot:
            solution.remove_job_from_slot(job)

        # Reassign the job to the original slot
        solution.assign_job_to_slot(job, from_slot)
        return solution

    def __repr__(self):
        return f"Step(description={self.description}, change={self.change})"


class TabuSearch:
    def __init__(
        self,
        initial_solution: List[int],
        evaluate: Callable[[List[int]], float],
        neighborhood_function: Callable[[List[int]], List[List[int]]],
        tabu_tenure: int = 10,
        max_iterations: int = 1000,
        aspiration_criteria: Callable[[float, float], bool] = None,
    ):
        """
        Initialize the Tabu Search algorithm.

        :param initial_solution: The starting solution.
        :param evaluate: A function that evaluates a solution and returns its cost.
        :param neighborhood_function: A function that generates neighboring solutions.
        :param tabu_tenure: The number of iterations a move should remain in the tabu list.
        :param max_iterations: Maximum number of iterations to run the algorithm.
        :param aspiration_criteria: A function that allows overriding the tabu status (optional).
        """
        self.current_solution = initial_solution
        self.evaluate = evaluate
        self.neighborhood_function = neighborhood_function
        self.tabu_list = deque(maxlen=tabu_tenure)
        self.max_iterations = max_iterations
        self.best_solution = initial_solution
        self.best_cost = evaluate(initial_solution)
        self.aspiration_criteria = aspiration_criteria

    def search(self) -> Tuple[List[int], float]:
        """
        Execute the Tabu Search algorithm.

        :return: The best solution found and its cost.
        """
        for iteration in range(self.max_iterations):
            neighbors = self.neighborhood_function(self.current_solution)
            best_neighbor = None
            best_neighbor_cost = float("inf")

            for neighbor in neighbors:
                if neighbor in self.tabu_list:
                    if self.aspiration_criteria and self.aspiration_criteria(self.evaluate(neighbor), self.best_cost):
                        continue  # Skip tabu move unless it meets the aspiration criteria
                cost = self.evaluate(neighbor)
                if cost < best_neighbor_cost:
                    best_neighbor = neighbor
                    best_neighbor_cost = cost

            if best_neighbor is not None:
                self.current_solution = best_neighbor
                self.tabu_list.append(best_neighbor)

                if best_neighbor_cost < self.best_cost:
                    self.best_solution = best_neighbor
                    self.best_cost = best_neighbor_cost

        return self.best_solution, self.best_cost


class TabuSearchScheduler:
    def __init__(self, job_collector, max_iterations=1000, tabu_size=20):
        self.job_collector = job_collector
        self.max_iterations = max_iterations
        self.tabu_size = tabu_size

    def schedule(self):
        best_solution = self.generate_initial_solution()
        best_cost = self.calculate_cost(best_solution)

        tabu_list = [best_solution]
        current_solution = best_solution

        for iteration in range(self.max_iterations):
            neighbors = self.generate_neighbors(current_solution)
            non_tabu_neighbors = [neighbor for neighbor in neighbors if neighbor not in tabu_list]

            if not non_tabu_neighbors:
                break

            current_solution = random.choice(non_tabu_neighbors)
            current_cost = self.calculate_cost(current_solution)

            if current_cost < best_cost:
                best_solution = current_solution
                best_cost = current_cost

            tabu_list.append(current_solution)
            if len(tabu_list) > self.tabu_size:
                tabu_list.pop(0)

        return best_solution

    def generate_initial_solution(self):
        # Randomly assign operations to time slots
        solution = {}
        for job in self.job_collector.jobs:
            for operation in job.route.operations:
                solution[(job.id, operation.id)] = random.randint(
                    0, self.job_collector.max_time - operation.processing_time
                )
        return solution

    def generate_neighbors(self, solution):
        neighbors = []
        for i in range(len(solution)):
            neighbor = solution.copy()
            job_id, operation_id = list(neighbor.keys())[i]
            operation = self.job_collector.get_operation_by_id(job_id, operation_id)
            neighbor[(job_id, operation_id)] = random.randint(
                0, self.job_collector.max_time - operation.processing_time
            )
            neighbors.append(neighbor)
        return neighbors

    def calculate_cost(self, solution):
        # Calculate the makespan of the schedule
        max_end_time = 0
        for job in self.job_collector.jobs:
            end_time = max(
                [solution[(job.id, operation.id)] + operation.processing_time for operation in job.route.operations]
            )
            max_end_time = max(max_end_time, end_time)
        return max_end_time


if __name__ == "__main__":
    initial_solution = [random.randint(0, 10) for _ in range(5)]
    print(initial_solution)
    tabu_search = TabuSearch(initial_solution, evaluate, neighborhood_function)
    best_solution, best_cost = tabu_search.search()

    print("Best Solution:", best_solution)
    print("Best Cost:", best_cost)
