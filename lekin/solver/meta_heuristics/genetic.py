"""Genetic scheduler"""

import copy
import random

from lekin.lekin_struct import JobCollector, ResourceCollector, RouteCollector


class GeneticScheduler:
    def __init__(
        self,
        job_collector: JobCollector,
        resource_collector: ResourceCollector,
        route_collector: RouteCollector = None,
        initial_schedule=None,
        **kwargs,
    ):
        self.job_collector = job_collector
        self.initial_schedule = initial_schedule
        self.optimizer = GeneticOPT()

    def parse_gene_permutation_to_solution(self):
        return


class GeneticOPT(object):
    def __init__(
        self,
        population_size=50,
        generations=1000,
        crossover_rate=0.8,
        mutation_rate=0.2,
    ):
        self.population_size = population_size
        self.generations = generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate

    def run(self):
        population = self.initialize_population()

        for generation in range(self.generations):
            selected_individuals = self.selection(population)
            new_population = []

            while len(new_population) < self.population_size:
                parent1 = random.choice(selected_individuals)
                parent2 = random.choice(selected_individuals)

                if random.random() < self.crossover_rate:
                    offspring1, offspring2 = self.crossover(parent1, parent2)
                else:
                    offspring1, offspring2 = parent1, parent2

                if random.random() < self.mutation_rate:
                    offspring1 = self.mutation(offspring1)
                if random.random() < self.mutation_rate:
                    offspring2 = self.mutation(offspring2)

                new_population.append(offspring1)
                new_population.append(offspring2)

            population = new_population

        # Find the best solution in the final population
        best_solution = min(population, key=lambda chromosome: self.fitness(chromosome)[0])

        # Return the best schedule
        return self.job_collector.create_schedule_from_operations(best_solution)

    def initialize_population(self):
        population = []
        for _ in range(self.population_size):
            # Shuffle the operations for each job to create a random chromosome
            chromosome = copy.deepcopy(self.job_collector.get_operations())
            for job_operations in chromosome.values():
                random.shuffle(job_operations)
            population.append(chromosome)
        return population

    def _init_ms(self):
        # ms_sequence: A list of resource IDs representing the machine sequence
        return

    def _init_os(self, jobs, resources):
        # os_sequence: A list of operation IDs representing the operation sequence.
        os_sequence = []
        ms_sequence = []

        all_operations = [op for job in jobs for group_op in job.group_operations for op in group_op.operations]
        random.shuffle(all_operations)
        for op in all_operations:
            os_sequence.append(op.operation_id)

            # Randomly assign a resource to each operation
            assigned_resource = random.choice(resources).resource_id
            ms_sequence.append(assigned_resource)

        return os_sequence, ms_sequence

    def fitness(self, chromosome):
        # Calculate the fitness of a chromosome based on the scheduling criteria (e.g., makespan, tardiness)
        # The lower the fitness value, the better the solution
        # Return a tuple with the fitness value and the schedule
        schedule = self.job_collector.create_schedule_from_operations(chromosome)
        fitness_value = 0
        return fitness_value, schedule

    def selection(self, population):
        # Select the best individuals based on their fitness values
        # You can use tournament selection, rank-based selection, or other methods
        # Return the selected individuals
        selected_individuals = 0
        return selected_individuals

    def crossover(self, parent1, parent2):
        # Perform crossover (recombination) between two parents to create two offspring
        # You can use one-point crossover, two-point crossover, or other methods
        # Return the two offspring
        offspring1, offspring2 = 0, 0
        return offspring1, offspring2

    def mutation(self, chromosome):
        # Introduce random changes in the chromosome to add diversity
        # You can swap two operations for a randomly selected job
        # Return the mutated chromosome
        mutated_chromosome = 0
        return mutated_chromosome

    # def decode(self):
    #     scheduling_result = SchedulingResult()
    #     resource_availability = {
    #         res.resource_id: 0 for res in resources
    #     }  # Tracks next available time for each resource
    #
    #     for op_id, res_id in zip(os_sequence, ms_sequence):
    #         op = operations[op_id]
    #         resource_ready_time = resource_availability[res_id]
    #         start_time = max(resource_ready_time, op.earliest_start)
    #         end_time = start_time + op.processing_time
    #
    #         # Update the schedule and resource availability
    #         scheduling_result.schedule[op_id] = (res_id, start_time, end_time)
    #         resource_availability[res_id] = end_time
    #
    #     return scheduling_result
