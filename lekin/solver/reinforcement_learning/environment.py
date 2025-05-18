"""
Environment class for reinforcement learning-based job shop scheduling.
"""

from dataclasses import dataclass
import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from lekin.lekin_struct.job import Job
from lekin.lekin_struct.operation import Operation
from lekin.lekin_struct.resource import Resource
from lekin.lekin_struct.route import Route
from lekin.solver.core.solution import Solution

logger = logging.getLogger(__name__)


@dataclass
class State:
    """Represents the state of the scheduling environment."""

    current_time: float
    available_jobs: List[Job]
    resource_states: Dict[str, List[Tuple[float, float]]]  # resource_id -> list of (start_time, end_time)
    job_completion: Dict[str, float]  # job_id -> completion time
    makespan: float
    tardiness: float
    resource_utilization: float

    def to_array(self) -> np.ndarray:
        """Convert state to a numpy array for the neural network.

        Returns:
            numpy array representation of the state
        """
        # Implement state vectorization here
        # This is a placeholder implementation
        return np.zeros(10)


class SchedulingEnvironment:
    """Environment for reinforcement learning-based job shop scheduling."""

    def __init__(self, jobs: List[Job], routes: List[Route], resources: List[Resource]):
        """Initialize the scheduling environment.

        Args:
            jobs: List of jobs to be scheduled
            routes: List of available routes
            resources: List of available resources
        """
        self.jobs = jobs
        self.routes = routes
        self.resources = resources
        self.solution = Solution(problem_id="rl_env", solver_type="q_learning")
        self.current_state = self._get_initial_state()

    def _get_initial_state(self) -> State:
        """Get the initial state of the environment.

        Returns:
            Initial state
        """
        return State(
            current_time=0.0,
            available_jobs=self.jobs.copy(),
            resource_states={r.resource_id: [] for r in self.resources},
            job_completion={},
            makespan=0.0,
            tardiness=0.0,
            resource_utilization=0.0,
        )

    def reset(self) -> State:
        """Reset the environment to its initial state.

        Returns:
            Initial state
        """
        self.solution = Solution(problem_id="rl_env", solver_type="q_learning")
        self.current_state = self._get_initial_state()
        return self.current_state

    def step(self, action: Job) -> Tuple[State, float, bool, Dict[str, Any]]:
        """Take a step in the environment by scheduling a job.

        Args:
            action: Job to schedule

        Returns:
            Tuple of (next_state, reward, done, info)
        """
        if action not in self.current_state.available_jobs:
            return self.current_state, -100.0, True, {"error": "Invalid action"}

        # Try to schedule the job
        success = self._schedule_job(action)
        if not success:
            return self.current_state, -50.0, False, {"error": "Scheduling failed"}

        # Update state
        self.current_state.available_jobs.remove(action)
        self.current_state = self._update_state()

        # Calculate reward
        reward = self._calculate_reward()

        # Check if episode is done
        done = len(self.current_state.available_jobs) == 0

        return self.current_state, reward, done, {}

    def _schedule_job(self, job: Job) -> bool:
        """Schedule a job in the current state.

        Args:
            job: Job to schedule

        Returns:
            True if scheduling was successful, False otherwise
        """
        try:
            # Find the route for this job
            route = next(r for r in job.routes if r.route_id == job.assigned_route_id)

            # Schedule each operation in the route
            current_time = self.current_state.current_time
            for operation in route.operations_sequence:
                # Find available resource and time slot
                resource, start_time = self._find_available_slot(operation, current_time)
                if not resource or start_time is None:
                    return False

                # Add assignment to solution
                self.solution.add_assignment(
                    operation_id=operation.operation_id,
                    job_id=job.job_id,
                    resource_id=resource.resource_id,
                    start_time=start_time,
                    end_time=start_time + operation.processing_time,
                    sequence_number=operation.sequence_number,
                )

                # Update resource state
                self.current_state.resource_states[resource.resource_id].append(
                    (start_time, start_time + operation.processing_time)
                )

                current_time = start_time + operation.processing_time

            # Update job completion time
            self.current_state.job_completion[job.job_id] = current_time
            return True

        except Exception as e:
            logger.error(f"Error scheduling job {job.job_id}: {str(e)}")
            return False

    def _find_available_slot(
        self, operation: Operation, current_time: float
    ) -> Tuple[Optional[Resource], Optional[float]]:
        """Find an available resource and time slot for an operation.

        Args:
            operation: Operation to schedule
            current_time: Current time in the schedule

        Returns:
            Tuple of (resource, start_time) if found, (None, None) otherwise
        """
        best_resource = None
        best_start_time = None
        best_score = float("inf")

        for resource in self.resources:
            if not self._is_resource_compatible(operation, resource):
                continue

            start_time = self._find_earliest_start_time(operation, resource, current_time)
            if start_time is None:
                continue

            score = self._evaluate_assignment(operation, resource, start_time)
            if score < best_score:
                best_score = score
                best_resource = resource
                best_start_time = start_time

        return best_resource, best_start_time

    def _is_resource_compatible(self, operation: Operation, resource: Resource) -> bool:
        """Check if a resource is compatible with an operation.

        Args:
            operation: Operation to check
            resource: Resource to check

        Returns:
            True if compatible, False otherwise
        """
        return operation.required_resource_type in resource.capabilities

    def _find_earliest_start_time(
        self, operation: Operation, resource: Resource, current_time: float
    ) -> Optional[float]:
        """Find the earliest possible start time for an operation on a resource.

        Args:
            operation: Operation to schedule
            resource: Resource to schedule on
            current_time: Current time in the schedule

        Returns:
            Earliest possible start time, or None if no time slot is available
        """
        # Sort existing assignments by start time
        assignments = sorted(self.current_state.resource_states[resource.resource_id], key=lambda x: x[0])

        # Find the first available slot
        for i in range(len(assignments)):
            if i == 0:
                if current_time + operation.processing_time <= assignments[0][0]:
                    return current_time
            else:
                if assignments[i - 1][1] + operation.processing_time <= assignments[i][0]:
                    return assignments[i - 1][1]

        # Check if we can schedule after the last assignment
        if not assignments or assignments[-1][1] + operation.processing_time <= float("inf"):
            return max(current_time, assignments[-1][1] if assignments else current_time)

        return None

    def _evaluate_assignment(self, operation: Operation, resource: Resource, start_time: float) -> float:
        """Evaluate the quality of a resource-time slot assignment.

        Args:
            operation: Operation to evaluate
            resource: Resource being considered
            start_time: Proposed start time

        Returns:
            Score (lower is better)
        """
        # Calculate various factors
        makespan_impact = start_time + operation.processing_time
        tardiness_impact = max(0, start_time + operation.processing_time - operation.due_date)
        utilization_impact = operation.processing_time / resource.capacity

        # Combine factors with weights
        return 0.4 * makespan_impact + 0.4 * tardiness_impact - 0.2 * utilization_impact

    def _update_state(self) -> State:
        """Update the current state based on the solution.

        Returns:
            Updated state
        """
        return State(
            current_time=max(self.current_state.job_completion.values()) if self.current_state.job_completion else 0.0,
            available_jobs=self.current_state.available_jobs,
            resource_states=self.current_state.resource_states,
            job_completion=self.current_state.job_completion,
            makespan=self.solution.get_makespan(),
            tardiness=self.solution.get_tardiness(),
            resource_utilization=self.solution.get_resource_utilization(),
        )

    def _calculate_reward(self) -> float:
        """Calculate the reward for the current state.

        Returns:
            Reward value
        """
        if not self.solution.assignments:
            return -100.0

        # Get metrics
        makespan = self.solution.get_makespan()
        tardiness = self.solution.get_tardiness()
        utilization = self.solution.get_resource_utilization()

        # Combine metrics into a single reward
        # Negative makespan and tardiness because we want to minimize them
        # Positive utilization because we want to maximize it
        reward = -0.4 * makespan - 0.4 * tardiness + 0.2 * utilization

        return reward

    def get_valid_actions(self) -> List[Job]:
        """Get the list of valid actions in the current state.

        Returns:
            List of valid jobs that can be scheduled
        """
        return self.current_state.available_jobs
