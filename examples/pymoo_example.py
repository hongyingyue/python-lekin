"""单资源优化
Use pymoo to do the job shop scheduling problem

存在一个资源上有若干任务
每个任务有自己的需求日期

目标为延误日期最少，同时换型最少
"""

from typing import Union

import numpy as np
from pymoo.algorithms.base.genetic import GeneticAlgorithm
from pymoo.algorithms.moo.nsga2 import NSGA2, RankAndCrowdingSurvival
from pymoo.algorithms.moo.nsga3 import NSGA3
from pymoo.algorithms.soo.nonconvex.ga import FitnessSurvival
from pymoo.core.crossover import Crossover
from pymoo.core.duplicate import DefaultDuplicateElimination, DuplicateElimination
from pymoo.core.mutation import Mutation
from pymoo.core.population import Population
from pymoo.core.problem import ElementwiseProblem, Problem
from pymoo.core.selection import Selection
from pymoo.core.survival import Survival
from pymoo.operators.crossover.binx import mut_binomial
from pymoo.operators.mutation.nom import NoMutation
from pymoo.operators.sampling.rnd import FloatRandomSampling
from pymoo.optimize import minimize
from pymoo.termination.default import DefaultSingleObjectiveTermination
from pymoo.util.display.output import Output
from pymoo.util.display.single import SingleObjectiveOutput


def main(resource, n_gen=5, seed=43, verbose=1):
    problem = CustomProblem(resource)
    # algorithm = CustomAlgorithm()
    algorithm = NSGA2(pop_size=10)
    res = minimize(problem, algorithm, termination=("n_gen", n_gen), seed=seed, verbose=verbose)
    print(res.X)
    order = problem.custom_object.get_order(res.X)

    print(order)


class CustomProblem(ElementwiseProblem):
    """问题定义函数"""

    def __init__(self, resource) -> None:
        # number of design variables
        n_var = len(resource.assigned_groupop)
        # number of objectives
        n_obj = 1
        # lower bounds of the design variables
        xl: Union[float, np.ndarray] = np.zeros(n_var)
        # upper bounds of the design variables
        xu: Union[float, np.ndarray] = np.ones(n_var)
        self.custom_object = CustomDecoder(resource)
        super().__init__(
            n_var=n_var,
            n_obj=n_obj,
            xl=xl,
            xu=xu,
        )

    def _evaluate(self, x, out):
        tardiness = self.custom_object.get_tardiness(x)
        # makespan = self.custom_object.get_makespan()
        # changeover = self.custom_object.get_changeover()
        out["F"] = [tardiness]


class CustomDecoder(object):
    """解码与目标函数"""

    def __init__(self, resource):
        self.resource = resource
        self.original_order = np.array(range(len(resource.assigned_groupop)))

    def get_order(self, x):
        idx = np.argsort(x)
        new_order = self.original_order[idx]
        return new_order

    def get_complete_time(self, new_order):
        time = 0

        for i in new_order:
            item = self.resource.assigned_groupop[i]
            item.assigned_start_time = time
            end = time + item.processing_hours
            item.assigned_end_time = end
            item.tardiness = max(0, end - item.demand_date)
            time = end

    def get_makespan(self):
        pass

    def get_tardiness(self, x):
        new_order = self.get_order(x)

        self.get_complete_time(new_order)
        tardiness: float = 0
        for item in self.resource.assigned_groupop:
            tardiness += item.tardiness
        print(new_order, tardiness)
        return tardiness

    def get_changeover(self):
        pass


# #
# class CustomAlgorithm(GeneticAlgorithm):
#     def __init__(self,
#                  pop_size=150,
#                  perc_elite=0.2,
#                  perc_mutants=0.1,
#                  bias=0.8,
#                  sampling=FloatRandomSampling(),
#                  survival=None,
#                  mutation=None,
#                  eliminate_duplicates=True,
#                  output=SingleObjectiveOutput(),
#                  ):
#         if perc_mutants + perc_elite >= 1.0:
#             raise ValueError("Elite and mutants can't be more than 100 percent of the population")
#
#         if survival is None:
#             survival = EliteSurvival(eliminate_duplicates=eliminate_duplicates)
#
#         if mutation is None:
#             mutation = NoMutation()
#
#         elite_size = int(pop_size * perc_elite)
#         n_mutants = int(pop_size * perc_mutants)
#         n_offsprings = pop_size - elite_size - n_mutants
#
#         super().__init__(
#             pop_size=pop_size,
#             n_offsprings=n_offsprings,
#             sampling=sampling,
#             selection=CustomSelection(elite_size),
#             crossover=CustomCrossOver(bias, n_offsprings=1, prob=1.0),
#             mutation=mutation,
#             survival=survival,
#             output=output,
#             eliminate_duplicates=True,
#             advance_after_initial_infill=True,
#         )
#
#         self.elite_size = elite_size
#         self.n_mutants = n_mutants
#         self.bias = bias
#         self.termination = DefaultSingleObjectiveTermination()
#
#
# class CustomSelection(Selection):
#     def __init__(self, elite_size, **kwargs) -> None:
#         super().__init__(**kwargs)
#         self.elite_size = elite_size
#
#     def _do(self, problem, pop, n_select, n_parents, **kwargs):
#         # do the mating selection - always one elite and one non-elites
#         s_elite = np.random.choice(np.arange(self.elite_size), size=n_select, replace=True)
#         s_non_elite = np.random.choice(np.arange(len(pop) - self.elite_size) + self.elite_size, size=n_select)
#
#         return np.column_stack([s_elite, s_non_elite])
#
#
# class CustomCrossOver(Crossover):
#     def __init__(self, bias=0.5, n_offsprings=2, **kwargs):
#         super().__init__(2, n_offsprings, **kwargs)
#         self.bias = bias
#
#     def _do(self, problem, X, **kwargs):
#         _, n_matings, n_var = X.shape
#
#         M = mut_binomial(n_matings, n_var, self.bias, at_least_once=True)
#         if self.n_offsprings == 1:
#             Xp = X[0].copy()
#             Xp[~M] = X[1][~M]
#             Xp = np.array([Xp])
#         elif self.n_offsprings == 2:
#             Xp = np.copy(X)
#             Xp[0][~M] = X[1][~M]
#             Xp[1][~M] = X[0][~M]
#         else:
#             raise Exception
#
#         return Xp
#
#
# class CustomMutation(Mutation):
#     def __init__(self):
#         super().__init__()
#
#     def _do(self, problem, X, **kwargs):
#         return
#
#
# class EliteSurvival(Survival):
#     def __init__(self, eliminate_duplicates=True, base_survival=None):
#         super().__init__(False)
#         if base_survival is None:
#             base_survival = FitnessSurvival()
#         self.base_survival = base_survival
#         if isinstance(eliminate_duplicates, bool) and eliminate_duplicates:
#             eliminate_duplicates = DefaultDuplicateElimination()
#         self.eliminate_duplicates = eliminate_duplicates
#
#     def _do(self, problem, pop, n_survive=None, algorithm=None, **kwargs):
#         # Do base survival (likely to be a sorting operator)
#         pop = self.base_survival.do(problem, pop)
#         pop = self.eliminate_duplicates.do(pop)
#
#         return pop
#
# class CustomOutput(Output):
#     pass


# ------------------------测试实例------------------------


class GroupOperation(object):
    def __init__(self, id, demand_date, processing_hours):
        self.id = id
        self.processing_hours = processing_hours
        self.demand_date = demand_date
        self.assigned_start_time = None
        self.assigned_end_time = None


class ResourceExtend(object):
    def __init__(self):
        self.assigned_groupop = []


groupop1 = GroupOperation(id=0, demand_date=4, processing_hours=3)
groupop2 = GroupOperation(id=1, demand_date=10, processing_hours=7)
groupop3 = GroupOperation(id=2, demand_date=15, processing_hours=6)
groupop4 = GroupOperation(id=3, demand_date=20, processing_hours=5)
groupop5 = GroupOperation(id=4, demand_date=20, processing_hours=3)

resource = ResourceExtend()
resource.assigned_groupop = [groupop4, groupop1, groupop2, groupop3]

main(resource)
