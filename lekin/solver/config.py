class SolverConfig:
    def __init__(self, optimization_strategy, entity_selector=None, move_selector=None, termination=None):
        self.optimization_strategy = optimization_strategy
        self.entity_selector = entity_selector
        self.move_selector = move_selector
        self.termination = termination


class TerminationConfig:
    def __init__(self, seconds_spent_limit=None, max_iterations=None):
        self.seconds_spent_limit = seconds_spent_limit
        self.max_iterations = max_iterations


class Message:
    def __init__(self, message: str):
        self.message = message

    def __repr__(self):
        return f"ErrorMessage(message={self.message})"
