"""
Agent class for reinforcement learning-based job shop scheduling.
"""

import logging
import random
from typing import Any, Dict, List, Optional, Tuple

import torch
import torch.nn as nn
import torch.optim as optim

from lekin.lekin_struct.job import Job
from lekin.solver.reinforcement_learning.environment import SchedulingEnvironment, State

logger = logging.getLogger(__name__)


class DQN(nn.Module):
    """Deep Q-Network for job shop scheduling."""

    def __init__(self, input_size: int, hidden_size: int, output_size: int):
        """Initialize the DQN.

        Args:
            input_size: Size of the input state vector
            hidden_size: Size of the hidden layer
            output_size: Size of the output action space
        """
        super(DQN, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, output_size),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through the network.

        Args:
            x: Input state tensor

        Returns:
            Q-values for each action
        """
        return self.network(x)


class ReplayBuffer:
    """Experience replay buffer for DQN training."""

    def __init__(self, capacity: int):
        """Initialize the replay buffer.

        Args:
            capacity: Maximum number of experiences to store
        """
        self.capacity = capacity
        self.buffer = []
        self.position = 0

    def push(self, state: State, action: Job, reward: float, next_state: State, done: bool):
        """Add an experience to the buffer.

        Args:
            state: Current state
            action: Action taken
            reward: Reward received
            next_state: Next state
            done: Whether the episode is done
        """
        if len(self.buffer) < self.capacity:
            self.buffer.append(None)
        self.buffer[self.position] = (state, action, reward, next_state, done)
        self.position = (self.position + 1) % self.capacity

    def sample(self, batch_size: int) -> List[Tuple[State, Job, float, State, bool]]:
        """Sample a batch of experiences from the buffer.

        Args:
            batch_size: Number of experiences to sample

        Returns:
            List of experience tuples
        """
        return random.sample(self.buffer, min(batch_size, len(self.buffer)))

    def __len__(self) -> int:
        """Get the current size of the buffer.

        Returns:
            Number of experiences in the buffer
        """
        return len(self.buffer)


class DQNAgent:
    """Deep Q-Learning agent for job shop scheduling."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the DQN agent.

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

        # Initialize networks and optimizer
        self.policy_net = None
        self.target_net = None
        self.optimizer = None
        self.memory = ReplayBuffer(self.buffer_size)
        self.steps_done = 0

    def initialize_networks(self, input_size: int, output_size: int):
        """Initialize the policy and target networks.

        Args:
            input_size: Size of the input state vector
            output_size: Size of the output action space
        """
        self.policy_net = DQN(input_size, self.hidden_size, output_size)
        self.target_net = DQN(input_size, self.hidden_size, output_size)
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
            for i, action in enumerate(valid_actions):
                mask[0, action.job_id] = 0

            q_values = q_values + mask
            action_idx = q_values.max(1)[1].item()

            return next(action for action in valid_actions if action.job_id == action_idx)

    def optimize_model(self):
        """Perform one step of optimization on the policy network."""
        if len(self.memory) < self.batch_size:
            return

        # Sample from replay buffer
        transitions = self.memory.sample(self.batch_size)
        batch = list(zip(*transitions))

        # Compute a mask of non-final states
        non_final_mask = torch.tensor(tuple(map(lambda s: s is not None, batch[3])), dtype=torch.bool)
        non_final_next_states = torch.FloatTensor([s.to_array() for s in batch[3] if s is not None])

        # Compute Q(s_t, a)
        state_batch = torch.FloatTensor([s.to_array() for s in batch[0]])
        action_batch = torch.LongTensor([[a.job_id] for a in batch[1]])
        reward_batch = torch.FloatTensor(batch[2])

        state_action_values = self.policy_net(state_batch).gather(1, action_batch)

        # Compute V(s_{t+1}) for all next states
        next_state_values = torch.zeros(self.batch_size)
        with torch.no_grad():
            next_state_values[non_final_mask] = self.target_net(non_final_next_states).max(1)[0]

        # Compute the expected Q values
        expected_state_action_values = (next_state_values * self.gamma) + reward_batch

        # Compute Huber loss
        criterion = nn.SmoothL1Loss()
        loss = criterion(state_action_values, expected_state_action_values.unsqueeze(1))

        # Optimize the model
        self.optimizer.zero_grad()
        loss.backward()
        for param in self.policy_net.parameters():
            param.grad.data.clamp_(-1, 1)
        self.optimizer.step()

        # Update epsilon
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

        # Update target network
        if self.steps_done % self.target_update == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())

        self.steps_done += 1

    def train(self, env: SchedulingEnvironment, num_episodes: int):
        """Train the agent.

        Args:
            env: The scheduling environment
            num_episodes: Number of episodes to train for
        """
        for episode in range(num_episodes):
            state = env.reset()
            total_reward = 0
            done = False

            while not done:
                # Select and perform an action
                action = self.select_action(state, env.get_valid_actions())
                next_state, reward, done, _ = env.step(action)

                # Store the transition in memory
                self.memory.push(state, action, reward, next_state, done)

                # Move to the next state
                state = next_state
                total_reward += reward

                # Perform one step of the optimization
                self.optimize_model()

            logger.info(f"Episode {episode + 1}/{num_episodes}, Total Reward: {total_reward:.2f}")

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
