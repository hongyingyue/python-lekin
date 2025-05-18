"""
Core solution representation for scheduling.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class OperationAssignment:
    """Represents the assignment of an operation to a resource and time slot."""

    operation_id: str
    job_id: str
    resource_id: str
    start_time: datetime
    end_time: datetime
    sequence_number: int = 0

    @property
    def duration(self) -> float:
        """Get the duration of the operation in hours."""
        return (self.end_time - self.start_time).total_seconds() / 3600


@dataclass
class Solution:
    """Represents a scheduling solution."""

    problem_id: str
    solver_type: str
    assignments: List[OperationAssignment] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_assignment(self, assignment: OperationAssignment) -> None:
        """Add an operation assignment to the solution.

        Args:
            assignment: The operation assignment to add
        """
        self.assignments.append(assignment)

    def get_assignments_by_job(self, job_id: str) -> List[OperationAssignment]:
        """Get all assignments for a specific job.

        Args:
            job_id: The ID of the job

        Returns:
            List of operation assignments for the job
        """
        return [a for a in self.assignments if a.job_id == job_id]

    def get_assignments_by_resource(self, resource_id: str) -> List[OperationAssignment]:
        """Get all assignments for a specific resource.

        Args:
            resource_id: The ID of the resource

        Returns:
            List of operation assignments for the resource
        """
        return [a for a in self.assignments if a.resource_id == resource_id]

    def get_resource_utilization(self, resource_id: str) -> float:
        """Calculate the utilization of a resource.

        Args:
            resource_id: The ID of the resource

        Returns:
            Resource utilization as a float between 0 and 1
        """
        resource_assignments = self.get_assignments_by_resource(resource_id)
        if not resource_assignments:
            return 0.0

        total_duration = sum(a.duration for a in resource_assignments)
        time_span = max(a.end_time for a in resource_assignments) - min(a.start_time for a in resource_assignments)
        return total_duration / time_span.total_seconds() * 3600

    def get_makespan(self) -> float:
        """Calculate the makespan of the solution.

        Returns:
            Makespan in hours
        """
        if not self.assignments:
            return 0.0

        return (
            max(a.end_time for a in self.assignments) - min(a.start_time for a in self.assignments)
        ).total_seconds() / 3600

    def get_tardiness(self) -> float:
        """Calculate the total tardiness of the solution.

        Returns:
            Total tardiness in hours
        """
        # Implement your tardiness calculation logic here
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert the solution to a dictionary representation.

        Returns:
            Dictionary representation of the solution
        """
        return {
            "problem_id": self.problem_id,
            "solver_type": self.solver_type,
            "assignments": [
                {
                    "operation_id": a.operation_id,
                    "job_id": a.job_id,
                    "resource_id": a.resource_id,
                    "start_time": a.start_time.isoformat(),
                    "end_time": a.end_time.isoformat(),
                    "sequence_number": a.sequence_number,
                }
                for a in self.assignments
            ],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Solution":
        """Create a solution from a dictionary representation.

        Args:
            data: Dictionary representation of the solution

        Returns:
            Solution instance
        """
        solution = cls(
            problem_id=data["problem_id"], solver_type=data["solver_type"], metadata=data.get("metadata", {})
        )

        for assignment_data in data["assignments"]:
            solution.add_assignment(
                OperationAssignment(
                    operation_id=assignment_data["operation_id"],
                    job_id=assignment_data["job_id"],
                    resource_id=assignment_data["resource_id"],
                    start_time=datetime.fromisoformat(assignment_data["start_time"]),
                    end_time=datetime.fromisoformat(assignment_data["end_time"]),
                    sequence_number=assignment_data.get("sequence_number", 0),
                )
            )

        return solution
