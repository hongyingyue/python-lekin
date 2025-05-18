"""Job Shop Scheduling Optimization Objectives Module.

This module provides a collection of objective functions and classes for evaluating
job shop scheduling solutions. It includes various metrics such as makespan,
tardiness, and resource utilization.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from lekin.objective.makespan import calculate_makespan
from lekin.objective.tardiness import (
    calculate_tardiness,
    calculate_total_late_jobs,
    calculate_total_late_time,
    calculate_total_tardiness,
)


@dataclass
class ObjectiveResult:
    """Container for objective function results."""

    value: float
    details: Dict[str, Any]
    is_feasible: bool = True


class SchedulingObjective(ABC):
    """Abstract base class for all scheduling objectives."""

    @abstractmethod
    def evaluate(self, schedule_result: Dict, job_collector: Any) -> ObjectiveResult:
        """Evaluate the objective function for a given schedule.

        Args:
            schedule_result: The schedule to evaluate
            job_collector: Collection of jobs and resources

        Returns:
            ObjectiveResult containing the evaluation results
        """
        pass


class MakespanObjective(SchedulingObjective):
    """Objective for minimizing the maximum completion time of all jobs."""

    def evaluate(self, schedule_result: Dict, job_collector: Any) -> ObjectiveResult:
        calculate_makespan(job_collector)
        max_makespan = max(job.makespan for job in job_collector.job_list)
        return ObjectiveResult(
            value=max_makespan,
            details={"job_makespans": {job.id: job.makespan for job in job_collector.job_list}},
            is_feasible=True,
        )


class TardinessObjective(SchedulingObjective):
    """Objective for minimizing job tardiness."""

    def __init__(self, objective_type: str = "total"):
        """Initialize tardiness objective.

        Args:
            objective_type: Type of tardiness metric ('total', 'max', 'weighted')
        """
        self.objective_type = objective_type

    def evaluate(self, schedule_result: Dict, job_collector: Any) -> ObjectiveResult:
        if self.objective_type == "total":
            value = calculate_total_tardiness(schedule_result, job_collector.job_list)
        elif self.objective_type == "late_jobs":
            value = calculate_total_late_jobs(schedule_result, job_collector.job_list)
        elif self.objective_type == "late_time":
            value = calculate_total_late_time(schedule_result, job_collector.job_list)
        else:
            raise ValueError(f"Unknown tardiness objective type: {self.objective_type}")

        return ObjectiveResult(value=value, details={"tardiness_type": self.objective_type}, is_feasible=True)


class ResourceUtilizationObjective(SchedulingObjective):
    """Objective for maximizing resource utilization."""

    def evaluate(self, schedule_result: Dict, job_collector: Any) -> ObjectiveResult:
        total_time = 0
        busy_time = 0

        for resource in job_collector.resources:
            for operation in schedule_result:
                if operation.resource == resource:
                    busy_time += operation.duration
                    total_time = max(total_time, operation.end_time)

        utilization = busy_time / (total_time * len(job_collector.resources)) if total_time > 0 else 0

        return ObjectiveResult(
            value=utilization,
            details={"total_time": total_time, "busy_time": busy_time, "resource_count": len(job_collector.resources)},
            is_feasible=True,
        )


class CompositeObjective(SchedulingObjective):
    """Combines multiple objectives with weights."""

    def __init__(self, objectives: List[tuple[SchedulingObjective, float]]):
        """Initialize composite objective.

        Args:
            objectives: List of (objective, weight) tuples
        """
        self.objectives = objectives

    def evaluate(self, schedule_result: Dict, job_collector: Any) -> ObjectiveResult:
        total_value = 0
        details = {}
        is_feasible = True

        for objective, weight in self.objectives:
            result = objective.evaluate(schedule_result, job_collector)
            total_value += weight * result.value
            details[objective.__class__.__name__] = result.details
            is_feasible = is_feasible and result.is_feasible

        return ObjectiveResult(value=total_value, details=details, is_feasible=is_feasible)
