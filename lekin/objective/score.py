from typing import List


class Score:
    def __init__(self, hard_score: int = 0, soft_score: int = 0):
        self.hard_score = hard_score  # Represents hard constraints violations
        self.soft_score = soft_score  # Represents soft constraints optimizations

    def __add__(self, other: "Score") -> "Score":
        return Score(hard_score=self.hard_score + other.hard_score, soft_score=self.soft_score + other.soft_score)

    def __sub__(self, other: "Score") -> "Score":
        return Score(hard_score=self.hard_score - other.hard_score, soft_score=self.soft_score - other.soft_score)

    def __lt__(self, other: "Score") -> bool:
        return (self.hard_score, self.soft_score) < (other.hard_score, other.soft_score)

    def __eq__(self, other: "Score") -> bool:
        return (self.hard_score, self.soft_score) == (other.hard_score, other.soft_score)

    def __repr__(self):
        return f"Score(hard_score={self.hard_score}, soft_score={self.soft_score})"

    def is_feasible(self) -> bool:
        """Check if the score is feasible (i.e., no hard constraint violations)."""
        return self.hard_score >= 0

    def total_score(self) -> int:
        """Compute the total score considering both hard and soft scores."""
        return self.hard_score + self.soft_score
