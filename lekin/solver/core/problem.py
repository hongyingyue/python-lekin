"""
Core problem representation for scheduling.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from lekin.lekin_struct.job import Job
from lekin.lekin_struct.resource import Resource
from lekin.lekin_struct.route import Route


@dataclass
class Problem:
    """Represents a scheduling problem instance."""

    jobs: List[Job]
    routes: List[Route]
    resources: List[Resource]
    config: Optional[Dict[str, Any]] = None

    def validate(self) -> bool:
        """Validate the problem instance.

        Returns:
            True if problem is valid, False otherwise
        """
        try:
            # Check if all required components are present
            if not self.jobs or not self.routes or not self.resources:
                return False

            # Validate job-route assignments
            for job in self.jobs:
                if not any(route.route_id == job.assigned_route_id for route in self.routes):
                    return False

            # Validate resource capabilities
            for route in self.routes:
                for operation in route.operations_sequence:
                    if not any(
                        resource.resource_id in [r.resource_id for r in operation.available_resource]
                        for resource in self.resources
                    ):
                        return False

            return True

        except Exception:
            return False

    def get_job_by_id(self, job_id: str) -> Optional[Job]:
        """Get a job by its ID.

        Args:
            job_id: The ID of the job to find

        Returns:
            The job if found, None otherwise
        """
        return next((job for job in self.jobs if job.job_id == job_id), None)

    def get_route_by_id(self, route_id: str) -> Optional[Route]:
        """Get a route by its ID.

        Args:
            route_id: The ID of the route to find

        Returns:
            The route if found, None otherwise
        """
        return next((route for route in self.routes if route.route_id == route_id), None)

    def get_resource_by_id(self, resource_id: str) -> Optional[Resource]:
        """Get a resource by its ID.

        Args:
            resource_id: The ID of the resource to find

        Returns:
            The resource if found, None otherwise
        """
        return next((resource for resource in self.resources if resource.resource_id == resource_id), None)

    def get_compatible_resources(self, operation) -> List[Resource]:
        """Get all resources compatible with an operation.

        Args:
            operation: The operation to find compatible resources for

        Returns:
            List of compatible resources
        """
        return [
            resource
            for resource in self.resources
            if resource.resource_id in [r.resource_id for r in operation.available_resource]
        ]

    def get_operation_sequence(self, job: Job) -> List[Any]:
        """Get the sequence of operations for a job.

        Args:
            job: The job to get operations for

        Returns:
            List of operations in sequence
        """
        route = self.get_route_by_id(job.assigned_route_id)
        if not route:
            return []
        return route.operations_sequence

    def get_time_window(self, job: Job) -> tuple[datetime, datetime]:
        """Get the time window for a job.

        Args:
            job: The job to get time window for

        Returns:
            Tuple of (earliest_start, latest_end)
        """
        # Implement your time window calculation logic here
        return job.release_date, job.demand_date
