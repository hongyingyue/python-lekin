"""
- 评估动作的价值，称为Q值：代表了智能体选择这个动作后，一直到最终状态奖励总和的期望；
- 评估状态的价值，称为V值：代表了智能体在这个状态下，一直到最终状态的奖励总和的期望
"""

import random

import numpy as np
import tensorflow as tf


class DeepQLearningScheduler:
    def __init__(
        self,
        job_collector,
        state_shape,
        action_shape,
        learning_rate=0.001,
        gamma=0.99,
        epsilon=1.0,
        epsilon_decay=0.995,
        epsilon_min=0.01,
    ):
        self.job_collector = job_collector
        self.state_shape = state_shape
        self.action_shape = action_shape
        self.learning_rate = learning_rate
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min

        self.memory = []
        self.q_network = self.build_q_network()
        self.target_q_network = self.build_q_network()
        self.update_target_network()

    def build_q_network(self):
        model = tf.keras.Sequential(
            [
                tf.keras.layers.Dense(64, activation="relu", input_shape=self.state_shape),
                tf.keras.layers.Dense(64, activation="relu"),
                tf.keras.layers.Dense(np.prod(self.action_shape), activation="linear"),
            ]
        )
        model.compile(optimizer=tf.keras.optimizers.Adam(lr=self.learning_rate), loss="mse")
        return model

    def update_target_network(self):
        self.target_q_network.set_weights(self.q_network.get_weights())

    def get_action(self, state):
        if np.random.rand() <= self.epsilon:
            return np.random.randint(0, np.prod(self.action_shape))
        return np.argmax(self.q_network.predict(np.array([state])))

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def replay(self, batch_size):
        if len(self.memory) < batch_size:
            return

        batch = random.sample(self.memory, batch_size)

        states = np.array([experience[0] for experience in batch])
        actions = np.array([experience[1] for experience in batch])
        rewards = np.array([experience[2] for experience in batch])
        next_states = np.array([experience[3] for experience in batch])
        dones = np.array([experience[4] for experience in batch])

        targets = rewards + self.gamma * (1 - dones) * np.amax(self.target_q_network.predict(next_states), axis=1)
        target_f = self.q_network.predict(states)
        target_f[np.arange(batch_size), actions] = targets

        self.q_network.fit(states, target_f, epochs=1, verbose=0)

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def train(self, episodes, batch_size):
        for episode in range(episodes):
            state = self.job_collector.get_state()
            done = False

            while not done:
                action = self.get_action(state)
                next_state, reward, done = self.job_collector.step(action)
                self.remember(state, action, reward, next_state, done)
                state = next_state

                if len(self.memory) > batch_size:
                    self.replay(batch_size)

            if episode % 10 == 0:
                self.update_target_network()

    def get_schedule(self):
        state = self.job_collector.get_state()
        done = False
        while not done:
            action = np.argmax(self.q_network.predict(np.array([state])))
            state, _, done = self.job_collector.step(action)
        return self.job_collector.get_schedule()
