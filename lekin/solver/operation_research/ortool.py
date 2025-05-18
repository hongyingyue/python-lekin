from ortools.sat.python import cp_model


class ORToolsScheduler:
    def __init__(self, job_collector):
        self.job_collector = job_collector
        self.model = cp_model.CpModel()
        self.vars = {}

    def schedule(self):
        self.create_variables()
        self.add_constraints()
        self.add_objective()
        solver = cp_model.CpSolver()
        status = solver.Solve(self.model)
        if status == cp_model.OPTIMAL:
            return self.get_schedule(solver)
        else:
            return None

    def create_variables(self):
        for job in self.job_collector.jobs:
            for operation in job.route.operations:
                self.vars[operation.id] = self.model.NewIntVar(
                    0, self.job_collector.max_time, f"Operation_{operation.id}_Start"
                )

    def add_constraints(self):
        for job in self.job_collector.jobs:
            for i, operation in enumerate(job.route.operations):
                # Constraint: Each operation starts after the end of its parent operation
                if i > 0:
                    parent_operation = job.route.operations[i - 1]
                    self.model.Add(
                        self.vars[operation.id] >= self.vars[parent_operation.id] + parent_operation.processing_time
                    )

                # Constraint: Each operation must be finished before the job's demand date
                self.model.Add(self.vars[operation.id] + operation.processing_time <= job.demand_date)

        for resource in self.job_collector.resources:
            for timeslot in resource.timeslots:
                for job in self.job_collector.jobs:
                    for operation in job.route.operations:
                        # Constraint: The operation must start within the resource's available timeslots
                        self.model.Add(self.vars[operation.id] >= timeslot.start_time).OnlyEnforceIf(timeslot.is_used)
                        self.model.Add(
                            self.vars[operation.id] <= timeslot.end_time - operation.processing_time
                        ).OnlyEnforceIf(timeslot.is_used)

    def add_objective(self):
        objective_var = self.model.NewIntVar(0, self.job_collector.max_time, "Makespan")
        self.model.AddMaxEquality(
            objective_var,
            [
                self.vars[operation.id] + operation.processing_time
                for job in self.job_collector.jobs
                for operation in job.route.operations
            ],
        )
        self.model.Minimize(objective_var)

    def get_schedule(self, solver):
        schedule = {}
        for job in self.job_collector.jobs:
            for operation in job.route.operations:
                start_time = solver.Value(self.vars[operation.id])
                schedule[(job.id, operation.id)] = start_time
        return schedule
