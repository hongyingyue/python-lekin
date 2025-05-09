import random
import sys

import numpy as np


class QLearningScheduler:
    def __init__(self, num_jobs, learning_rate=0.1, discount_factor=0.8, epsilon=1.0, epsilon_decay=0.999):
        self.num_jobs = num_jobs
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.Q = np.zeros((num_jobs, num_jobs))  # Assuming a Q-table where rows and columns represent jobs
        self.V = np.zeros(num_jobs)

    def choose_action(self, current_job, possible_jobs):
        """
        Choose the next job based on the epsilon-greedy policy.
        """
        if random.uniform(0, 1) < self.epsilon:
            # Exploration: choose a random job
            next_job = random.choice(possible_jobs)
        else:
            # Exploitation: choose the best job based on Q values
            next_job_values = self.Q[current_job, possible_jobs]
            next_job = possible_jobs[np.argmax(next_job_values)]
        return next_job

    def update_Q(self, current_job, next_job, reward):
        """
        Update the Q-table based on the action taken and the reward received.
        """
        td_target = reward + self.discount_factor * np.max(self.Q[next_job])
        td_error = td_target - self.Q[current_job, next_job]
        self.Q[current_job, next_job] += self.learning_rate * td_error

    def update_V(self, job, reward):
        """
        Update the value (V) of being in a specific job.
        """
        # Direct update to V, considering the immediate reward and discounting the best future value achievable
        best_future_value = np.max(self.Q[job])
        self.V[job] += self.learning_rate * (reward + self.discount_factor * best_future_value - self.V[job])

    def update_epsilon(self):
        """
        Apply decay to epsilon to reduce exploration over time.
        """
        self.epsilon *= self.epsilon_decay


def permutation(j, V, Q, epsilon):
    # It generates a permutation (sequence) of jobs based on the current Q-values and a vector
    # V, which represents the estimated value of being in each state (job)
    vec = j[:]  # j: A list representing the original order of jobs.
    # A matrix of Q-values, where Q[i][j] represents the value of choosing job j after job i.
    Q_temp = [[Q[x][y] for y in range(len(Q[0]))] for x in range(len(Q))]
    for i in j:
        # for job i in sequence j, select the next job based on the Q-values/V (exploitation) or randomly (exploration).
        # This decision is made by comparing a random number to epsilon.
        if random.uniform(0, 1) > epsilon:  # larger than epsilon represent choosing by best way
            if j.index(i) == 0:  # if it is the first choice, according to V
                temp = V.index(min(float(s) for s in V))
                for k in range(0, len(Q_temp[0])):
                    Q_temp[k][temp] = sys.maxsize
                a, b = 0, vec.index(temp)
                vec[b], vec[a] = vec[a], vec[b]
            else:  # else according to Q
                temp = Q_temp[i - 1].index(lowest_cost(Q_temp, i - 1))
                for k in range(0, len(Q_temp[0])):
                    Q_temp[k][temp] = sys.maxsize
                a, b = i, vec.index(temp)
                vec[b], vec[a] = vec[a], vec[b]
        else:  # else by random
            temp = random.choice(vec)
            a, b = i, vec.index(temp)
            vec[b], vec[a] = vec[a], vec[b]
    return vec


# update Q
def update_Q(Q, r, cost):
    # update the Q-values based on the latest information obtained from taking an action
    # Q_table[state, action] = reward + np.max(Q_table[next_state])
    gamma = 0.8  # discount factor, the importance of future rewards
    alpha = 0.1  # learning rate, how much of the new information will override the old information
    # r: A list representing the sequence (order) of jobs that were scheduled. It reflects the recent action
    for i in range(0, len(r) - 1):
        # current Q-value for scheduling job + alpha * temporal difference error (TD error)
        Q[r[i]][r[i + 1]] = Q[r[i]][r[i + 1]] + alpha * (cost + gamma * lowest_cost(Q, r[i]) - Q[r[i]][r[i + 1]])
    return Q


# update V
def update_V(V, Q, r, cost):
    gamma = 0.8
    alpha = 0.1
    V[r[0]] = V[r[0]] + alpha * (cost + gamma * lowest_cost(Q, r[0]) - V[r[0]])
    return V


def lowest_cost(Q, r):
    cost = sys.maxsize
    for i in range(0, len(Q[0])):
        if Q[r][i] < cost:
            cost = Q[r][i]
    return cost
