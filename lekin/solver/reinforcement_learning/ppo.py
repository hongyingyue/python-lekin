"""
Proximal Policy Optimization (PPO) implementation for job shop scheduling.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
from torch.distributions import Categorical
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

from lekin.lekin_struct.job import Job
from lekin.solver.reinforcement_learning.environment import SchedulingEnvironment, State

logger = logging.getLogger(__name__)


class ActorCritic(nn.Module):
    """Actor-Critic network for PPO."""

    def __init__(self, input_size: int, hidden_size: int, output_size: int):
        """Initialize the Actor-Critic network.

        Args:
            input_size: Size of the input state vector
            hidden_size: Size of the hidden layers
            output_size: Size of the output action space
        """
        super(ActorCritic, self).__init__()

        # Shared feature layers
        self.feature_layer = nn.Sequential(
            nn.Linear(input_size, hidden_size), nn.ReLU(), nn.Linear(hidden_size, hidden_size), nn.ReLU()
        )

        # Actor head (policy)
        self.actor = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2), nn.ReLU(), nn.Linear(hidden_size // 2, output_size)
        )

        # Critic head (value)
        self.critic = nn.Sequential(nn.Linear(hidden_size, hidden_size // 2), nn.ReLU(), nn.Linear(hidden_size // 2, 1))

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Forward pass through the network.

        Args:
            x: Input state tensor

        Returns:
            Tuple of (action probabilities, state value)
        """
        features = self.feature_layer(x)
        action_probs = F.softmax(self.actor(features), dim=-1)
        state_value = self.critic(features)
        return action_probs, state_value


class PPOMemory:
    """Memory buffer for PPO training."""

    def __init__(self, batch_size: int):
        """Initialize the PPO memory buffer.

        Args:
            batch_size: Size of each training batch
        """
        self.states = []
        self.actions = []
        self.probs = []
        self.vals = []
        self.rewards = []
        self.dones = []
        self.batch_size = batch_size

    def push(self, state: State, action: Job, probs: float, val: float, reward: float, done: bool):
        """Add a transition to the memory buffer.

        Args:
            state: Current state
            action: Action taken
            probs: Action probabilities
            val: State value
            reward: Reward received
            done: Whether the episode is done
        """
        self.states.append(state)
        self.actions.append(action)
        self.probs.append(probs)
        self.vals.append(val)
        self.rewards.append(reward)
        self.dones.append(done)

    def get_batches(self) -> List[Tuple]:
        """Get batches of experiences for training.

        Returns:
            List of experience batches
        """
        n_states = len(self.states)
        batch_start = np.arange(0, n_states, self.batch_size)
        indices = np.arange(n_states, dtype=np.int64)
        np.random.shuffle(indices)
        batches = [indices[i : i + self.batch_size] for i in batch_start]

        return [
            (self.states[b], self.actions[b], self.probs[b], self.vals[b], self.rewards[b], self.dones[b])
            for b in batches
        ]

    def clear(self):
        """Clear the memory buffer."""
        self.states = []
        self.actions = []
        self.probs = []
        self.vals = []
        self.rewards = []
        self.dones = []


class PPOAgent:
    """PPO agent for job shop scheduling."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the PPO agent.

        Args:
            config: Optional configuration dictionary with the following keys:
                - learning_rate: float, learning rate for the optimizer (default: 0.0003)
                - gamma: float, discount factor (default: 0.99)
                - gae_lambda: float, GAE-Lambda parameter (default: 0.95)
                - policy_clip: float, PPO clip parameter (default: 0.2)
                - batch_size: int, size of training batches (default: 64)
                - n_epochs: int, number of epochs to train on each batch (default: 10)
                - hidden_size: int, size of hidden layers (default: 128)
                - entropy_coef: float, entropy coefficient for exploration (default: 0.01)
                - value_coef: float, value loss coefficient (default: 0.5)
                - max_grad_norm: float, maximum gradient norm (default: 0.5)
        """
        self.config = config or {}
        self.learning_rate = self.config.get("learning_rate", 0.0003)
        self.gamma = self.config.get("gamma", 0.99)
        self.gae_lambda = self.config.get("gae_lambda", 0.95)
        self.policy_clip = self.config.get("policy_clip", 0.2)
        self.batch_size = self.config.get("batch_size", 64)
        self.n_epochs = self.config.get("n_epochs", 10)
        self.hidden_size = self.config.get("hidden_size", 128)
        self.entropy_coef = self.config.get("entropy_coef", 0.01)
        self.value_coef = self.config.get("value_coef", 0.5)
        self.max_grad_norm = self.config.get("max_grad_norm", 0.5)

        # Initialize network and optimizer
        self.actor_critic = None
        self.optimizer = None
        self.memory = PPOMemory(self.batch_size)

    def initialize_networks(self, input_size: int, output_size: int):
        """Initialize the actor-critic network.

        Args:
            input_size: Size of the input state vector
            output_size: Size of the output action space
        """
        self.actor_critic = ActorCritic(input_size, self.hidden_size, output_size)
        self.optimizer = optim.Adam(self.actor_critic.parameters(), lr=self.learning_rate)

    def select_action(self, state: State, valid_actions: List[Job]) -> Tuple[Job, float, float]:
        """Select an action using the current policy.

        Args:
            state: Current state
            valid_actions: List of valid actions

        Returns:
            Tuple of (selected action, action probability, state value)
        """
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state.to_array()).unsqueeze(0)
            action_probs, state_value = self.actor_critic(state_tensor)

            # Mask invalid actions
            mask = torch.ones_like(action_probs) * float("-inf")
            for action in valid_actions:
                mask[0, action.job_id] = 0

            # Apply mask and renormalize
            masked_probs = F.softmax(action_probs + mask, dim=-1)

            # Sample action
            dist = Categorical(masked_probs)
            action_idx = dist.sample().item()

            # Get selected action and its probability
            selected_action = next(action for action in valid_actions if action.job_id == action_idx)
            action_prob = masked_probs[0, action_idx].item()

            return selected_action, action_prob, state_value.item()

    def compute_gae(
        self, rewards: List[float], values: List[float], dones: List[bool]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Compute Generalized Advantage Estimation.

        Args:
            rewards: List of rewards
            values: List of state values
            dones: List of done flags

        Returns:
            Tuple of (advantages, returns)
        """
        advantages = np.zeros(len(rewards), dtype=np.float32)
        returns = np.zeros(len(rewards), dtype=np.float32)
        gae = 0

        for t in reversed(range(len(rewards))):
            if t == len(rewards) - 1:
                next_value = 0
            else:
                next_value = values[t + 1]

            delta = rewards[t] + self.gamma * next_value * (1 - dones[t]) - values[t]
            gae = delta + self.gamma * self.gae_lambda * (1 - dones[t]) * gae
            advantages[t] = gae

        returns = advantages + values
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        return advantages, returns

    def learn(self):
        """Perform one learning step."""
        for _ in range(self.n_epochs):
            for batch in self.memory.get_batches():
                states, actions, old_probs, old_vals, rewards, dones = batch

                # Convert to tensors
                states = torch.FloatTensor([s.to_array() for s in states])
                actions = torch.LongTensor([[a.job_id] for a in actions])
                old_probs = torch.FloatTensor(old_probs)
                old_vals = torch.FloatTensor(old_vals)

                # Compute GAE
                advantages, returns = self.compute_gae(rewards, old_vals, dones)
                advantages = torch.FloatTensor(advantages)
                returns = torch.FloatTensor(returns)

                # Get new action probabilities and values
                new_probs, new_vals = self.actor_critic(states)
                new_probs = new_probs.gather(1, actions).squeeze()

                # Calculate ratios
                ratio = torch.exp(torch.log(new_probs) - torch.log(old_probs))

                # Calculate surrogate losses
                surr1 = ratio * advantages
                surr2 = torch.clamp(ratio, 1 - self.policy_clip, 1 + self.policy_clip) * advantages

                # Calculate final losses
                policy_loss = -torch.min(surr1, surr2).mean()
                value_loss = F.mse_loss(new_vals.squeeze(), returns)
                entropy_loss = -torch.mean(torch.sum(new_probs * torch.log(new_probs + 1e-10), dim=1))

                # Total loss
                loss = policy_loss + self.value_coef * value_loss - self.entropy_coef * entropy_loss

                # Optimize
                self.optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.actor_critic.parameters(), self.max_grad_norm)
                self.optimizer.step()

        self.memory.clear()

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
                # Select action
                action, prob, val = self.select_action(state, env.get_valid_actions())

                # Take action
                next_state, reward, done, _ = env.step(action)

                # Store transition
                self.memory.push(state, action, prob, val, reward, done)

                # Update state and reward
                state = next_state
                total_reward += reward

            # Learn from collected experiences
            self.learn()

            # Update best reward and save model if improved
            if total_reward > best_reward:
                best_reward = total_reward
                self.save("best_model.pt")

            reward_history.append(total_reward)
            avg_reward = sum(reward_history[-100:]) / min(len(reward_history), 100)

            logger.info(
                f"Episode {episode + 1}/{num_episodes}, "
                f"Total Reward: {total_reward:.2f}, "
                f"Average Reward: {avg_reward:.2f}"
            )

    def save(self, path: str):
        """Save the agent's model.

        Args:
            path: Path to save the model to
        """
        torch.save(
            {
                "actor_critic_state_dict": self.actor_critic.state_dict(),
                "optimizer_state_dict": self.optimizer.state_dict(),
            },
            path,
        )

    def load(self, path: str):
        """Load the agent's model.

        Args:
            path: Path to load the model from
        """
        checkpoint = torch.load(path)
        self.actor_critic.load_state_dict(checkpoint["actor_critic_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
