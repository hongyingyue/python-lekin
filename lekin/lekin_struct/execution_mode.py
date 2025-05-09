from typing import List, Optional


class ExecutionMode:
    def __init__(self, id: str, job, duration: int, resource_requirements: Optional[List] = None):
        self.id = id
        self.job = job
        self.duration = duration
        self.resource_requirements = resource_requirements if resource_requirements else []

    def __repr__(self):
        return f"ExecutionMode(id={self.id}, duration={self.duration})"
