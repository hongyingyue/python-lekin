"""
Advanced Deep Q-Network implementation for job shop scheduling.
"""

from collections import namedtuple
import logging
import random
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset

from lekin.lekin_struct.job import Job
from lekin.solver.reinforcement_learning.environment import SchedulingEnvironment, State

logger = logging.getLogger(__name__)

# Define experience tuple
Experience = namedtuple("Experience", ["state", "action", "reward", "next_state", "done"])


class PrioritizedReplayBuffer:
    """Prioritized experience replay buffer for DQN training."""

    def __init__(self, capacity: int, alpha: float = 0.6, beta: float = 0.4):
        """Initialize the prioritized replay buffer.

        Args:
            capacity: Maximum number of experiences to store
            alpha: Priority exponent (0 = uniform sampling, 1 = fully prioritized)
            beta: Importance sampling exponent (0 = no correction, 1 = full correction)
        """
        self.capacity = capacity
        self.alpha = alpha
        self.beta = beta
        self.buffer = []
        self.priorities = np.zeros(capacity)
        self.position = 0
        self.max_priority = 1.0

    def push(self, experience: Experience, error: float = None):
        """Add an experience to the buffer.

        Args:
            experience: Experience tuple to add
            error: TD error for priority calculation (if None, use max priority)
        """
        if len(self.buffer) < self.capacity:
            self.buffer.append(None)

        self.buffer[self.position] = experience
        priority = self.max_priority if error is None else (abs(error) + 1e-6) ** self.alpha
        self.priorities[self.position] = priority
        self.position = (self.position + 1) % self.capacity

    def sample(self, batch_size: int) -> Tuple[List[Experience], np.ndarray, np.ndarray]:
        """Sample a batch of experiences from the buffer.

        Args:
            batch_size: Number of experiences to sample

        Returns:
            Tuple of (experiences, indices, weights)
        """
        if len(self.buffer) == self.capacity:
            priorities = self.priorities
        else:
            priorities = self.priorities[: len(self.buffer)]

        # Calculate sampling probabilities
        probs = priorities / priorities.sum()
        indices = np.random.choice(len(self.buffer), batch_size, p=probs)

        # Calculate importance sampling weights
        weights = (len(self.buffer) * probs[indices]) ** (-self.beta)
        weights = weights / weights.max()

        experiences = [self.buffer[idx] for idx in indices]
        return experiences, indices, weights

    def update_priorities(self, indices: np.ndarray, errors: np.ndarray):
        """Update priorities for experiences.

        Args:
            indices: Indices of experiences to update
            errors: New TD errors for these experiences
        """
        for idx, error in zip(indices, errors):
            priority = (abs(error) + 1e-6) ** self.alpha
            self.priorities[idx] = priority
            self.max_priority = max(self.max_priority, priority)

    def __len__(self) -> int:
        """Get the current size of the buffer.

        Returns:
            Number of experiences in the buffer
        """
        return len(self.buffer)


class DuelingDQN(nn.Module):
    """Dueling Deep Q-Network for job shop scheduling."""

    def __init__(self, input_size: int, hidden_size: int, output_size: int):
        """Initialize the Dueling DQN.

        Args:
            input_size: Size of the input state vector
            hidden_size: Size of the hidden layers
            output_size: Size of the output action space
        """
        super(DuelingDQN, self).__init__()

        # Feature layers
        self.feature_layer = nn.Sequential(
            nn.Linear(input_size, hidden_size), nn.ReLU(), nn.Linear(hidden_size, hidden_size), nn.ReLU()
        )

        # Value stream
        self.value_stream = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2), nn.ReLU(), nn.Linear(hidden_size // 2, 1)
        )

        # Advantage stream
        self.advantage_stream = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2), nn.ReLU(), nn.Linear(hidden_size // 2, output_size)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through the network.

        Args:
            x: Input state tensor

        Returns:
            Q-values for each action
        """
        features = self.feature_layer(x)

        # Calculate value and advantage
        value = self.value_stream(features)
        advantage = self.advantage_stream(features)

        # Combine value and advantage
        # Q(s,a) = V(s) + (A(s,a) - mean(A(s,a)))
        return value + (advantage - advantage.mean(dim=1, keepdim=True))


class DoubleDQNAgent:
    """Double DQN agent with dueling architecture and prioritized replay."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Double DQN agent.

        Args:
            config: Optional configuration dictionary with the following keys:
                - learning_rate: float, learning rate for the optimizer (default: 0.001)
                - gamma: float, discount factor (default: 0.99)
                - epsilon: float, exploration rate (default: 1.0)
                - epsilon_decay: float, decay rate for exploration (default: 0.995)
                - epsilon_min: float, minimum exploration rate (default: 0.01)
                - batch_size: int, size of training batches (default: 64)
                - buffer_size: int, size of replay buffer (default: 10000)
                - target_update: int, frequency of target network updates (default: 10)
                - hidden_size: int, size of hidden layers (default: 128)
                - alpha: float, priority exponent (default: 0.6)
                - beta: float, importance sampling exponent (default: 0.4)
                - beta_increment: float, beta increment per update (default: 0.001)
                - grad_clip: float, gradient clipping value (default: 1.0)
        """
        self.config = config or {}
        self.learning_rate = self.config.get("learning_rate", 0.001)
        self.gamma = self.config.get("gamma", 0.99)
        self.epsilon = self.config.get("epsilon", 1.0)
        self.epsilon_decay = self.config.get("epsilon_decay", 0.995)
        self.epsilon_min = self.config.get("epsilon_min", 0.01)
        self.batch_size = self.config.get("batch_size", 64)
        self.buffer_size = self.config.get("buffer_size", 10000)
        self.target_update = self.config.get("target_update", 10)
        self.hidden_size = self.config.get("hidden_size", 128)
        self.alpha = self.config.get("alpha", 0.6)
        self.beta = self.config.get("beta", 0.4)
        self.beta_increment = self.config.get("beta_increment", 0.001)
        self.grad_clip = self.config.get("grad_clip", 1.0)

        # Initialize networks and optimizer
        self.policy_net = None
        self.target_net = None
        self.optimizer = None
        self.memory = PrioritizedReplayBuffer(self.buffer_size, self.alpha, self.beta)
        self.steps_done = 0

    def initialize_networks(self, input_size: int, output_size: int):
        """Initialize the policy and target networks.

        Args:
            input_size: Size of the input state vector
            output_size: Size of the output action space
        """
        self.policy_net = DuelingDQN(input_size, self.hidden_size, output_size)
        self.target_net = DuelingDQN(input_size, self.hidden_size, output_size)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=self.learning_rate)

    def select_action(self, state: State, valid_actions: List[Job]) -> Job:
        """Select an action using epsilon-greedy policy.

        Args:
            state: Current state
            valid_actions: List of valid actions

        Returns:
            Selected action
        """
        if random.random() < self.epsilon:
            return random.choice(valid_actions)

        with torch.no_grad():
            state_tensor = torch.FloatTensor(state.to_array()).unsqueeze(0)
            q_values = self.policy_net(state_tensor)

            # Mask invalid actions with large negative values
            mask = torch.ones_like(q_values) * float("-inf")
            for action in valid_actions:
                mask[0, action.job_id] = 0

            q_values = q_values + mask
            action_idx = q_values.max(1)[1].item()

            return next(action for action in valid_actions if action.job_id == action_idx)

    def optimize_model(self):
        """Perform one step of optimization on the policy network."""
        if len(self.memory) < self.batch_size:
            return

        # Sample from replay buffer
        experiences, indices, weights = self.memory.sample(self.batch_size)
        batch = Experience(*zip(*experiences))
        weights = torch.FloatTensor(weights)

        # Compute a mask of non-final states
        non_final_mask = torch.tensor(tuple(map(lambda s: s is not None, batch.next_state)), dtype=torch.bool)
        non_final_next_states = torch.FloatTensor([s.to_array() for s in batch.next_state if s is not None])

        # Compute Q(s_t, a)
        state_batch = torch.FloatTensor([s.to_array() for s in batch.state])
        action_batch = torch.LongTensor([[a.job_id] for a in batch.action])
        reward_batch = torch.FloatTensor(batch.reward)

        # Double DQN: Use policy network to select actions, target network to evaluate
        with torch.no_grad():
            # Select actions using policy network
            next_actions = self.policy_net(non_final_next_states).max(1)[1].unsqueeze(1)
            # Evaluate actions using target network
            next_state_values = torch.zeros(self.batch_size)
            next_state_values[non_final_mask] = (
                self.target_net(non_final_next_states).gather(1, next_actions).squeeze(1)
            )

        # Compute expected Q values
        expected_state_action_values = (next_state_values * self.gamma) + reward_batch

        # Compute current Q values
        state_action_values = self.policy_net(state_batch).gather(1, action_batch)

        # Compute TD errors for priority update
        td_errors = (expected_state_action_values.unsqueeze(1) - state_action_values).detach().numpy()

        # Update priorities
        self.memory.update_priorities(indices, td_errors)

        # Compute weighted Huber loss
        criterion = nn.SmoothL1Loss(reduction="none")
        loss = (criterion(state_action_values, expected_state_action_values.unsqueeze(1)) * weights.unsqueeze(1)).mean()

        # Optimize the model
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), self.grad_clip)
        self.optimizer.step()

        # Update epsilon
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

        # Update target network
        if self.steps_done % self.target_update == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())

        # Update beta
        self.beta = min(1.0, self.beta + self.beta_increment)

        self.steps_done += 1

    def train(self, env: SchedulingEnvironment, num_episodes: int):
        """Train the agent.

        Args:
            env: The scheduling environment
            num_episodes: Number of episodes to train for
        """
        best_reward = float("-inf")
        reward_history = []

        for episode in range(num_episodes):
            state = env.reset()
            total_reward = 0
            done = False

            while not done:
                # Select and perform an action
                action = self.select_action(state, env.get_valid_actions())
                next_state, reward, done, _ = env.step(action)

                # Store the transition in memory
                self.memory.push(Experience(state, action, reward, next_state, done))

                # Move to the next state
                state = next_state
                total_reward += reward

                # Perform one step of the optimization
                self.optimize_model()

            # Update best reward and save model if improved
            if total_reward > best_reward:
                best_reward = total_reward
                self.save("best_model.pt")

            reward_history.append(total_reward)
            avg_reward = sum(reward_history[-100:]) / min(len(reward_history), 100)

            logger.info(
                f"Episode {episode + 1}/{num_episodes}, "
                f"Total Reward: {total_reward:.2f}, "
                f"Average Reward: {avg_reward:.2f}, "
                f"Epsilon: {self.epsilon:.3f}"
            )

    def save(self, path: str):
        """Save the agent's model.

        Args:
            path: Path to save the model to
        """
        torch.save(
            {
                "policy_net_state_dict": self.policy_net.state_dict(),
                "target_net_state_dict": self.target_net.state_dict(),
                "optimizer_state_dict": self.optimizer.state_dict(),
                "epsilon": self.epsilon,
                "steps_done": self.steps_done,
                "beta": self.beta,
            },
            path,
        )

    def load(self, path: str):
        """Load the agent's model.

        Args:
            path: Path to load the model from
        """
        checkpoint = torch.load(path)
        self.policy_net.load_state_dict(checkpoint["policy_net_state_dict"])
        self.target_net.load_state_dict(checkpoint["target_net_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.epsilon = checkpoint["epsilon"]
        self.steps_done = checkpoint["steps_done"]
        self.beta = checkpoint.get("beta", self.beta)
