import copy
import random
import time


def check_constraints(job_assignments):
    for i, assignment1 in enumerate(job_assignments):
        for j, assignment2 in enumerate(job_assignments):
            if i < j:
                # Check resource conflict
                if assignment1.resource == assignment2.resource:
                    if not (
                        assignment1.timeslot.end_time <= assignment2.timeslot.start_time
                        or assignment2.timeslot.end_time <= assignment1.timeslot.start_time
                    ):
                        return False
                # Check timeslot conflict
                if assignment1.timeslot is None or assignment2.timeslot is None:
                    return False
    return True


class LekinSolver(object):
    def __init__(self, config):
        self.config = config
        self.best_solution = None

    def solve(self, schedule):
        start_time = time.time()
        current_solution = copy.deepcopy(schedule)
        self.best_solution = current_solution
        tabu_list = []
        iterations = 0

        while not self._is_termination_reached(start_time, iterations):
            neighbors = self.config.move_selector.generate_neighbors(current_solution)
            feasible_neighbors = [neighbor for neighbor in neighbors if check_constraints(neighbor.job_assignments)]

            if not feasible_neighbors:
                continue

            feasible_neighbors.sort(key=self.config.entity_selector.evaluate)
            current_solution = feasible_neighbors[0]
            current_cost = self.config.entity_selector.evaluate(current_solution)
            best_cost = self.config.entity_selector.evaluate(self.best_solution)

            if current_cost < best_cost:
                self.best_solution = current_solution

            tabu_list.append(current_solution)
            if len(tabu_list) > self.config.entity_selector.tabu_tenure:
                tabu_list.pop(0)

            iterations += 1

        return self.best_solution

    def _is_termination_reached(self, start_time, iterations):
        if self.config.termination.seconds_spent_limit:
            if time.time() - start_time > self.config.termination.seconds_spent_limit:
                return True
        if self.config.termination.max_iterations:
            if iterations >= self.config.termination.max_iterations:
                return True
        return False
