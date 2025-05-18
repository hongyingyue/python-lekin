"""
Concrete implementation of the CTP (Continuous Time Planning) solver.
"""

from datetime import datetime
import heapq
import logging
from typing import Any, Dict, List, Optional, Tuple

from lekin.lekin_struct.job import Job
from lekin.lekin_struct.operation import Operation
from lekin.lekin_struct.resource import Resource
from lekin.lekin_struct.route import Route
from lekin.solver.core.base_solver import BaseSolver
from lekin.solver.utils.constraint_checker import ConstraintChecker
from lekin.solver.utils.time_slot import TimeSlot

logger = logging.getLogger(__name__)


class CTPSolver(BaseSolver):
    """Continuous Time Planning solver implementation."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the CTP solver.

        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)
        self.constraint_checker = ConstraintChecker()

    def solve(self, jobs: List[Job], routes: List[Route], resources: List[Resource]) -> Dict[str, Any]:
        """Solve the scheduling problem using CTP approach.

        Args:
            jobs: List of jobs to be scheduled
            routes: List of available routes
            resources: List of available resources

        Returns:
            Dictionary containing the solution and metadata
        """
        try:
            # Sort jobs based on priority and constraints
            sorted_jobs = self._sort_jobs(jobs)

            solution = {"scheduled_operations": [], "resource_assignments": {}, "makespan": 0.0, "metadata": {}}

            for job in sorted_jobs:
                route = self._find_route(job, routes)
                if not route:
                    logger.warning(f"No valid route found for job {job.job_id}")
                    continue

                # Process operations in reverse order (from end to start)
                operations = route.operations_sequence[::-1]
                current_end_time = job.demand_date

                for operation in operations:
                    success = self._schedule_operation(
                        operation=operation,
                        job=job,
                        current_end_time=current_end_time,
                        resources=resources,
                        solution=solution,
                    )

                    if not success:
                        logger.warning(f"Failed to schedule operation {operation.operation_id} for job {job.job_id}")
                        # Implement rescheduling logic here
                        break

            return solution

        except Exception as e:
            logger.error(f"Error in CTP solver: {str(e)}")
            raise

    def validate_solution(self, solution: Dict[str, Any]) -> bool:
        """Validate if the solution meets all constraints.

        Args:
            solution: The solution to validate

        Returns:
            True if solution is valid, False otherwise
        """
        try:
            return self.constraint_checker.validate_solution(solution)
        except Exception as e:
            logger.error(f"Error validating solution: {str(e)}")
            return False

    def _sort_jobs(self, jobs: List[Job]) -> List[Job]:
        """Sort jobs based on priority and constraints.

        Args:
            jobs: List of jobs to sort

        Returns:
            Sorted list of jobs
        """

        def job_key(job: Job) -> Tuple[float, datetime]:
            return (job.priority, job.demand_date)

        return sorted(jobs, key=job_key)

    def _find_route(self, job: Job, routes: List[Route]) -> Optional[Route]:
        """Find the appropriate route for a job.

        Args:
            job: The job to find route for
            routes: List of available routes

        Returns:
            The matching route or None if not found
        """
        for route in routes:
            if route.route_id == job.assigned_route_id:
                return route
        return None

    def _schedule_operation(
        self,
        operation: Operation,
        job: Job,
        current_end_time: datetime,
        resources: List[Resource],
        solution: Dict[str, Any],
    ) -> bool:
        """Schedule a single operation.

        Args:
            operation: The operation to schedule
            job: The parent job
            current_end_time: The latest allowed end time
            resources: Available resources
            solution: Current solution being built

        Returns:
            True if operation was scheduled successfully, False otherwise
        """
        try:
            # Find best resource and time slot
            resource, time_slot = self._find_best_resource_and_timeslot(
                operation=operation, resources=resources, latest_end_time=current_end_time
            )

            if not resource or not time_slot:
                return False

            # Assign operation to resource
            operation.assigned_resource = resource
            operation.assigned_timeslot = time_slot

            # Update solution
            solution["scheduled_operations"].append(
                {
                    "operation_id": operation.operation_id,
                    "job_id": job.job_id,
                    "resource_id": resource.resource_id,
                    "start_time": time_slot.start_time,
                    "end_time": time_slot.end_time,
                }
            )

            # Update resource assignments
            if resource.resource_id not in solution["resource_assignments"]:
                solution["resource_assignments"][resource.resource_id] = []
            solution["resource_assignments"][resource.resource_id].append(operation.operation_id)

            return True

        except Exception as e:
            logger.error(f"Error scheduling operation {operation.operation_id}: {str(e)}")
            return False

    def _find_best_resource_and_timeslot(
        self, operation: Operation, resources: List[Resource], latest_end_time: datetime
    ) -> Tuple[Optional[Resource], Optional[TimeSlot]]:
        """Find the best resource and time slot for an operation.

        Args:
            operation: The operation to schedule
            resources: Available resources
            latest_end_time: Latest allowed end time

        Returns:
            Tuple of (best_resource, best_time_slot) or (None, None) if no valid assignment found
        """
        best_score = float("inf")
        best_resource = None
        best_time_slot = None

        for resource in resources:
            if not self._is_resource_compatible(resource, operation):
                continue

            time_slots = self._find_available_time_slots(
                resource=resource, operation=operation, latest_end_time=latest_end_time
            )

            for time_slot in time_slots:
                score = self._evaluate_assignment(operation, resource, time_slot)
                if score < best_score:
                    best_score = score
                    best_resource = resource
                    best_time_slot = time_slot

        return best_resource, best_time_slot

    def _is_resource_compatible(self, resource: Resource, operation: Operation) -> bool:
        """Check if a resource is compatible with an operation.

        Args:
            resource: The resource to check
            operation: The operation to check

        Returns:
            True if resource is compatible, False otherwise
        """
        return resource.resource_id in [r.resource_id for r in operation.available_resource]

    def _find_available_time_slots(
        self, resource: Resource, operation: Operation, latest_end_time: datetime
    ) -> List[TimeSlot]:
        """Find available time slots for an operation on a resource.

        Args:
            resource: The resource to check
            operation: The operation to schedule
            latest_end_time: Latest allowed end time

        Returns:
            List of available time slots
        """
        available_slots = []
        required_duration = self._calculate_operation_duration(operation)

        for slot in resource.available_timeslots:
            if slot.end_time <= latest_end_time and slot.duration >= required_duration:
                available_slots.append(slot)

        return available_slots

    def _calculate_operation_duration(self, operation: Operation) -> float:
        """Calculate the duration of an operation.

        Args:
            operation: The operation to calculate duration for

        Returns:
            Duration in hours
        """
        if hasattr(operation.beat_time, "__iter__"):
            return (operation.beat_time[0] * operation.quantity) / 60
        return operation.processing_time

    def _evaluate_assignment(self, operation: Operation, resource: Resource, time_slot: TimeSlot) -> float:
        """Evaluate the quality of a resource-time slot assignment.

        Args:
            operation: The operation to evaluate
            resource: The resource being considered
            time_slot: The time slot being considered

        Returns:
            Score (lower is better)
        """
        # Implement your evaluation logic here
        # Consider factors like:
        # - Changeover time
        # - Resource utilization
        # - Time to deadline
        # - Priority
        return 0.0  # Placeholder
