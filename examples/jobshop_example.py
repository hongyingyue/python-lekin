"""Demo"""

import copy

from lekin.solver.config import SolverConfig, TerminationConfig
from lekin.solver.solver import LekinSolver


def PlanningEntity(cls):
    cls._is_planning_entity = True
    return cls


def PlanningSolution(cls):
    cls._is_planning_solution = True
    return cls


@PlanningEntity
class Job:
    def __init__(self, id, name):
        self.id = id
        self.name = name


@PlanningEntity
class Resource:
    def __init__(self, id, name):
        self.id = id
        self.name = name


@PlanningEntity
class Timeslot:
    def __init__(self, id, start_time, end_time):
        self.id = id
        self.start_time = start_time
        self.end_time = end_time


@PlanningEntity
class JobAssignment:
    def __init__(self, job, resource=None, timeslot=None):
        self.job = job
        self.resource = resource
        self.timeslot = timeslot


@PlanningSolution
class JobSchedule:
    def __init__(self, job_assignments, resources, timeslots):
        self.job_assignments = job_assignments
        self.resources = resources
        self.timeslots = timeslots


class TabuSearchEntitySelector:
    def __init__(self, tabu_tenure=10):
        self.tabu_tenure = tabu_tenure

    def evaluate(self, job_schedule):
        # Objective: minimize the total usage of timeslots (example)
        return sum(
            [
                assignment.timeslot.end_time - assignment.timeslot.start_time
                for assignment in job_schedule.job_assignments
                if assignment.timeslot
            ]
        )


class NeighborMoveSelector:
    def generate_neighbors(self, job_schedule):
        neighbors = []
        for assignment in job_schedule.job_assignments:
            for resource in job_schedule.resources:
                for timeslot in job_schedule.timeslots:
                    new_assignment = copy.deepcopy(assignment)
                    new_assignment.resource = resource
                    new_assignment.timeslot = timeslot
                    new_job_assignments = copy.deepcopy(job_schedule.job_assignments)
                    new_job_assignments[job_schedule.job_assignments.index(assignment)] = new_assignment
                    neighbors.append(JobSchedule(new_job_assignments, job_schedule.resources, job_schedule.timeslots))
        return neighbors


if __name__ == "__main__":
    jobs = [Job(1, "Job1"), Job(2, "Job2")]
    resources = [Resource(1, "Resource1"), Resource(2, "Resource2")]
    timeslots = [Timeslot(1, 8, 10), Timeslot(2, 10, 12)]

    job_assignments = [JobAssignment(job) for job in jobs]
    job_schedule = JobSchedule(job_assignments, resources, timeslots)

    entity_selector = TabuSearchEntitySelector(tabu_tenure=10)
    move_selector = NeighborMoveSelector()
    termination_config = TerminationConfig(seconds_spent_limit=10, max_iterations=100)

    solver_config = SolverConfig(
        entity_selector=entity_selector, move_selector=move_selector, termination=termination_config
    )
    solver = LekinSolver(solver_config)

    solution = solver.solve(job_schedule)

    if solution:
        for assignment in solution.job_assignments:
            if assignment.resource:
                print(
                    f"Job {assignment.job.name} assigned to Resource {assignment.resource.name} at "
                    f"Timeslot {assignment.timeslot.id}"
                )
