"""
Q-Learning based solver for job shop scheduling problems.
"""

import logging
from typing import Any, Dict, List, Optional

import numpy as np

from lekin.lekin_struct.job import Job
from lekin.lekin_struct.operation import Operation
from lekin.lekin_struct.resource import Resource
from lekin.lekin_struct.route import Route
from lekin.solver.core.base_solver import BaseSolver
from lekin.solver.core.solution import Solution
from lekin.solver.reinforcement_learning.agent import DQNAgent
from lekin.solver.reinforcement_learning.environment import SchedulingEnvironment

logger = logging.getLogger(__name__)


class QLearningSolver(BaseSolver):
    """Q-Learning based solver for job shop scheduling problems."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Q-Learning solver.

        Args:
            config: Optional configuration dictionary with the following keys:
                - learning_rate: float, learning rate for Q-learning (default: 0.001)
                - gamma: float, discount factor (default: 0.99)
                - epsilon: float, exploration rate (default: 1.0)
                - epsilon_decay: float, decay rate for exploration (default: 0.995)
                - epsilon_min: float, minimum exploration rate (default: 0.01)
                - batch_size: int, size of training batches (default: 64)
                - buffer_size: int, size of replay buffer (default: 10000)
                - target_update: int, frequency of target network updates (default: 10)
                - hidden_size: int, size of hidden layers (default: 128)
                - num_episodes: int, number of training episodes (default: 1000)
                - model_path: str, path to save/load the trained model (default: None)
        """
        super().__init__(config)
        self.agent = DQNAgent(config)
        self.num_episodes = self.config.get("num_episodes", 1000)
        self.model_path = self.config.get("model_path")

    def solve(self, jobs: List[Job], routes: List[Route], resources: List[Resource]) -> Solution:
        """Solve the scheduling problem using Q-Learning.

        Args:
            jobs: List of jobs to be scheduled
            routes: List of available routes
            resources: List of available resources

        Returns:
            A solution to the scheduling problem
        """
        # Create environment
        env = SchedulingEnvironment(jobs, routes, resources)

        # Initialize agent networks if not loaded from file
        if not self.model_path:
            input_size = 10  # Size of state vector
            output_size = len(jobs)  # Number of possible actions
            self.agent.initialize_networks(input_size, output_size)

            # Train the agent
            logger.info("Starting training...")
            self.agent.train(env, self.num_episodes)

            # Save the trained model if path is provided
            if self.model_path:
                self.agent.save(self.model_path)
        else:
            # Load pre-trained model
            self.agent.load(self.model_path)

        # Use the trained agent to find the best solution
        best_solution = None
        best_makespan = float("inf")

        # Run multiple episodes to find the best solution
        for _ in range(10):
            state = env.reset()
            done = False

            while not done:
                action = self.agent.select_action(state, env.get_valid_actions())
                state, _, done, _ = env.step(action)

            solution = env.solution
            makespan = solution.get_makespan()

            if makespan < best_makespan:
                best_makespan = makespan
                best_solution = solution

            logger.info(f"Trial makespan: {makespan:.2f}")

        if not best_solution:
            raise RuntimeError("Failed to find a valid solution")

        return best_solution

    def validate_solution(self, solution: Solution) -> bool:
        """Validate if a solution meets all constraints.

        Args:
            solution: The solution to validate

        Returns:
            True if solution is valid, False otherwise
        """
        if not solution.assignments:
            return False

        # Check for resource conflicts
        resource_assignments = {}
        for assignment in solution.assignments:
            if assignment.resource_id not in resource_assignments:
                resource_assignments[assignment.resource_id] = []
            resource_assignments[assignment.resource_id].append(assignment)

        # Check for overlapping assignments on the same resource
        for resource_id, assignments in resource_assignments.items():
            assignments.sort(key=lambda x: x.start_time)
            for i in range(len(assignments) - 1):
                if assignments[i].end_time > assignments[i + 1].start_time:
                    return False

        return True
