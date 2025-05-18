"""
Operation Relations Module

This module defines the relationships between operations in a job shop scheduling problem.
These relationships determine how operations are scheduled relative to each other.

The module supports various types of relationships:
- ES (End-Start): Predecessor must finish before successor can start
- ES-Split: Successor starts after all split operations of predecessor complete
- SS (Start-Start): Operations can start simultaneously
- SS-Split: Successor starts with the last split operation of predecessor
- EE (End-End): Operations must finish together
- EE-Split: Successor's end time depends on predecessor's split operations
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class RelationType(Enum):
    """Types of relationships between operations."""

    ES = "ES"  # End-Start: Predecessor must finish before successor can start
    ES_SPLIT = "ES-Split"  # Successor starts after all split operations complete
    SS = "SS"  # Start-Start: Operations can start simultaneously
    SS_SPLIT = "SS-Split"  # Successor starts with last split operation
    EE = "EE"  # End-End: Operations must finish together
    EE_SPLIT = "EE-Split"  # Successor's end time depends on split operations
    EE_SS = "EE-SS"  # Special case where successor must start with predecessor


@dataclass
class OperationRelation:
    """Represents a relationship between two operations.

    Attributes:
        relation_type (RelationType): Type of relationship between operations
        predecessor_id (str): ID of the predecessor operation
        successor_id (str): ID of the successor operation
        lag_time (float): Minimum time required between operations
        lead_time (float): Maximum time allowed between operations
        split_operations (Optional[List[str]]): IDs of split operations if applicable
    """

    relation_type: RelationType
    predecessor_id: str
    successor_id: str
    lag_time: float = 0.0
    lead_time: float = 0.0
    split_operations: Optional[List[str]] = None

    def __post_init__(self):
        """Validate the operation relation after initialization."""
        if not isinstance(self.relation_type, RelationType):
            raise ValueError("relation_type must be a RelationType enum")
        if not isinstance(self.predecessor_id, str) or not self.predecessor_id:
            raise ValueError("predecessor_id must be a non-empty string")
        if not isinstance(self.successor_id, str) or not self.successor_id:
            raise ValueError("successor_id must be a non-empty string")
        if self.lag_time < 0:
            raise ValueError("lag_time must be non-negative")
        if self.lead_time < 0:
            raise ValueError("lead_time must be non-negative")
        if self.split_operations and not all(isinstance(op_id, str) for op_id in self.split_operations):
            raise ValueError("split_operations must be a list of strings")

    def calculate_start_time(self, predecessor_end_time: datetime) -> datetime:
        """Calculate the earliest start time for the successor operation.

        Args:
            predecessor_end_time: The end time of the predecessor operation

        Returns:
            datetime: The earliest start time for the successor operation
        """
        if self.relation_type in [RelationType.ES, RelationType.ES_SPLIT]:
            return predecessor_end_time + self.lag_time
        return predecessor_end_time

    def calculate_end_time(self, predecessor_end_time: datetime) -> datetime:
        """Calculate the required end time for the successor operation.

        Args:
            predecessor_end_time: The end time of the predecessor operation

        Returns:
            datetime: The required end time for the successor operation
        """
        if self.relation_type in [RelationType.EE, RelationType.EE_SPLIT]:
            return predecessor_end_time
        return predecessor_end_time + self.lead_time

    def __repr__(self) -> str:
        return (
            f"OperationRelation(type={self.relation_type.value}, "
            f"predecessor={self.predecessor_id}, successor={self.successor_id})"
        )


class RelationManager:
    """Manages relationships between operations in the scheduling system.

    This class provides methods to store, retrieve, and manage operation
    relationships, ensuring proper scheduling constraints are maintained.

    Attributes:
        relations (Dict[str, List[OperationRelation]]): Map of operation IDs to their relationships
    """

    def __init__(self):
        """Initialize an empty relation manager."""
        self.relations: Dict[str, List[OperationRelation]] = {}

    def add_relation(self, relation: OperationRelation) -> None:
        """Add a relationship between operations.

        Args:
            relation: The operation relation to add
        """
        if not isinstance(relation, OperationRelation):
            raise TypeError("relation must be an OperationRelation instance")

        # Add to predecessor's relations
        if relation.predecessor_id not in self.relations:
            self.relations[relation.predecessor_id] = []
        self.relations[relation.predecessor_id].append(relation)

        # Add to successor's relations
        if relation.successor_id not in self.relations:
            self.relations[relation.successor_id] = []
        self.relations[relation.successor_id].append(relation)

    def get_relations_for_operation(self, operation_id: str) -> List[OperationRelation]:
        """Get all relationships for a specific operation.

        Args:
            operation_id: The ID of the operation

        Returns:
            List[OperationRelation]: List of relationships for the operation
        """
        return self.relations.get(operation_id, [])

    def get_predecessors(self, operation_id: str) -> List[str]:
        """Get all predecessor operation IDs for a specific operation.

        Args:
            operation_id: The ID of the operation

        Returns:
            List[str]: List of predecessor operation IDs
        """
        return [rel.predecessor_id for rel in self.relations.get(operation_id, []) if rel.successor_id == operation_id]

    def get_successors(self, operation_id: str) -> List[str]:
        """Get all successor operation IDs for a specific operation.

        Args:
            operation_id: The ID of the operation

        Returns:
            List[str]: List of successor operation IDs
        """
        return [rel.successor_id for rel in self.relations.get(operation_id, []) if rel.predecessor_id == operation_id]

    def clear(self) -> None:
        """Clear all relationships from the manager."""
        self.relations.clear()
