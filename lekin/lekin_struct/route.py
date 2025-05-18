"""
Route module for representing operation sequences in job shop scheduling.

This module provides the Route class and RouteCollector for managing operation sequences
and their associated resources in the scheduling process.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from lekin.lekin_struct.exceptions import ValidationError
from lekin.lekin_struct.operation import Operation
from lekin.lekin_struct.resource import Resource
from lekin.lekin_struct.timeslot import TimeSlot


@dataclass
class Route:
    """Represents a sequence of operations in the scheduling process.

    A route defines the order in which operations should be performed and
    specifies which resources are available for each operation.

    Attributes:
        route_id (str): Unique identifier for the route
        operations_sequence (List[Operation]): Ordered list of operations
        available_resources (List[Resource]): List of resources that can perform operations
        available_time_slots (List[TimeSlot]): List of available time slots
        metadata (Dict[str, Any]): Additional metadata for the route
    """

    route_id: str
    operations_sequence: List[Operation] = field(default_factory=list)
    available_resources: List[Resource] = field(default_factory=list)
    available_time_slots: List[TimeSlot] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate route attributes after initialization."""
        if not isinstance(self.route_id, str) or not self.route_id:
            raise ValidationError("route_id must be a non-empty string")
        if not all(isinstance(op, Operation) for op in self.operations_sequence):
            raise ValidationError("All operations must be Operation instances")
        if not all(isinstance(res, Resource) for res in self.available_resources):
            raise ValidationError("All resources must be Resource instances")
        if not all(isinstance(ts, TimeSlot) for ts in self.available_time_slots):
            raise ValidationError("All time slots must be TimeSlot instances")

    def add_operation(self, operation: Operation) -> None:
        """Add an operation to the sequence.

        Args:
            operation: The operation to add

        Raises:
            ValidationError: If operation is not an Operation instance
        """
        if not isinstance(operation, Operation):
            raise ValidationError("operation must be an Operation instance")
        self.operations_sequence.append(operation)

    def get_operations(self) -> List[Operation]:
        """Get the sequence of operations.

        Returns:
            List[Operation]: The sequence of operations
        """
        return self.operations_sequence

    def add_resource(self, resource: Resource) -> None:
        """Add a resource to the available resources.

        Args:
            resource: The resource to add

        Raises:
            ValidationError: If resource is not a Resource instance
        """
        if not isinstance(resource, Resource):
            raise ValidationError("resource must be a Resource instance")
        self.available_resources.append(resource)

    def add_time_slot(self, time_slot: TimeSlot) -> None:
        """Add a time slot to the available time slots.

        Args:
            time_slot: The time slot to add

        Raises:
            ValidationError: If time_slot is not a TimeSlot instance
        """
        if not isinstance(time_slot, TimeSlot):
            raise ValidationError("time_slot must be a TimeSlot instance")
        self.available_time_slots.append(time_slot)

    def get_total_processing_time(self) -> float:
        """Calculate total processing time for all operations.

        Returns:
            float: Total processing time
        """
        return sum(op.processing_time for op in self.operations_sequence)

    def get_operation_by_id(self, operation_id: str) -> Optional[Operation]:
        """Get an operation by its ID.

        Args:
            operation_id: ID of the operation to find

        Returns:
            Optional[Operation]: The found operation or None
        """
        return next((op for op in self.operations_sequence if op.operation_id == operation_id), None)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Route):
            return NotImplemented
        return self.route_id == other.route_id

    def __hash__(self) -> int:
        return hash(self.route_id)

    def __str__(self) -> str:
        return f"Route(id={self.route_id})"

    def __repr__(self) -> str:
        return (
            f"Route(route_id='{self.route_id}', "
            f"operations={[op.operation_id for op in self.operations_sequence]}, "
            f"resources={[res.resource_id for res in self.available_resources]})"
        )


@dataclass
class RouteCollector:
    """Manages collections of routes in the scheduling system.

    This class provides methods to store, retrieve, and manage routes
    across different jobs. It maintains a centralized registry of all
    routes for efficient access and management.

    Attributes:
        routes (Dict[str, Route]): Map of route IDs to routes
    """

    routes: Dict[str, Route] = field(default_factory=dict)

    def add_route(self, route: Route) -> None:
        """Add a route to the collector.

        Args:
            route: The route to add

        Raises:
            ValidationError: If route is not a Route instance or if route_id already exists
        """
        if not isinstance(route, Route):
            raise ValidationError("route must be a Route instance")
        if route.route_id in self.routes:
            raise ValidationError(f"Route with ID {route.route_id} already exists")
        self.routes[route.route_id] = route

    def get_route_by_id(self, route_id: str) -> Optional[Route]:
        """Get a route by its ID.

        Args:
            route_id: ID of the route to find

        Returns:
            Optional[Route]: The found route or None
        """
        return self.routes.get(route_id)

    def get_all_routes(self) -> List[Route]:
        """Get all routes in the collector.

        Returns:
            List[Route]: List of all routes
        """
        return list(self.routes.values())

    def remove_route(self, route_id: str) -> None:
        """Remove a route from the collector.

        Args:
            route_id: ID of the route to remove

        Raises:
            KeyError: If route_id does not exist
        """
        if route_id not in self.routes:
            raise KeyError(f"Route with ID {route_id} does not exist")
        del self.routes[route_id]

    def __iter__(self):
        """Iterate over all routes."""
        return iter(self.routes.values())

    def __len__(self) -> int:
        """Get the number of routes in the collector."""
        return len(self.routes)

    def __str__(self) -> str:
        return f"RouteCollector(routes={len(self.routes)})"

    def __repr__(self) -> str:
        return f"RouteCollector(routes={list(self.routes.keys())})"
