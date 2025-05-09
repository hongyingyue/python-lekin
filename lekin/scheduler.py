"""Flexible job shop scheduler
Rescheduler due to inserted order or default machine
"""

from collections import OrderedDict
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

from lekin.datasets.check_data import check_data


class Scheduler(object):
    def __init__(self, objective, solver, max_operations, **kwargs):
        self.objective = objective
        self.solver = solver
        self.max_operations = max_operations

    def run(self, jobs, machines):
        self.solver.solve(jobs, machines)

    def evaluate(self):
        pass

    def plot(self):
        pass
