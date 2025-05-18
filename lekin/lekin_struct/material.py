"""
Material module for managing materials and inventory in job shop scheduling.

This module provides classes for representing materials, their requirements,
and inventory management in a manufacturing environment.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from lekin.lekin_struct.exceptions import ValidationError


class MaterialType(Enum):
    """Types of materials in the manufacturing process."""

    RAW = "raw"
    COMPONENT = "component"
    FINISHED = "finished"
    CONSUMABLE = "consumable"


@dataclass
class Material:
    """Represents a material used in manufacturing.

    A material can be raw material, component, finished product, or consumable.
    Each material has properties like type, unit, and constraints that affect
    scheduling and inventory management.

    Attributes:
        material_id (str): Unique identifier for the material
        name (str): Human-readable name of the material
        material_type (MaterialType): Type of the material
        unit (str): Unit of measurement (e.g., kg, pieces)
        min_quantity (float): Minimum quantity that must be maintained
        max_quantity (float): Maximum quantity that can be stored
        lead_time (float): Time required to procure the material
        shelf_life (Optional[float]): Shelf life in days, if applicable
        supplier_info (Optional[Dict[str, Any]]): Information about suppliers
        properties (Dict[str, Any]): Additional material properties
    """

    material_id: str
    name: str
    material_type: MaterialType
    unit: str
    min_quantity: float = 0.0
    max_quantity: float = float("inf")
    lead_time: float = 0.0
    shelf_life: Optional[float] = None
    supplier_info: Optional[Dict[str, Any]] = None
    properties: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate material attributes after initialization."""
        if not isinstance(self.material_id, str) or not self.material_id:
            raise ValidationError("material_id must be a non-empty string")
        if not isinstance(self.name, str) or not self.name:
            raise ValidationError("name must be a non-empty string")
        if not isinstance(self.material_type, MaterialType):
            raise ValidationError("material_type must be a MaterialType enum")
        if self.min_quantity < 0:
            raise ValidationError("min_quantity must be non-negative")
        if self.max_quantity <= self.min_quantity:
            raise ValidationError("max_quantity must be greater than min_quantity")
        if self.lead_time < 0:
            raise ValidationError("lead_time must be non-negative")
        if self.shelf_life is not None and self.shelf_life <= 0:
            raise ValidationError("shelf_life must be positive if specified")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Material):
            return NotImplemented
        return self.material_id == other.material_id

    def __hash__(self) -> int:
        return hash(self.material_id)

    def __str__(self) -> str:
        return f"Material(id={self.material_id}, name={self.name}, type={self.material_type.value})"

    def __repr__(self) -> str:
        return (
            f"Material(material_id='{self.material_id}', name='{self.name}', "
            f"material_type={self.material_type}, unit='{self.unit}')"
        )


@dataclass
class MaterialInventory:
    """Manages inventory levels and material availability.

    This class tracks current inventory levels, handles material reservations,
    and manages material requirements for jobs.

    Attributes:
        materials (Dict[str, Material]): Dictionary of available materials
        current_levels (Dict[str, float]): Current inventory levels
        reserved_quantities (Dict[str, float]): Quantities reserved for jobs
        last_updated (datetime): Timestamp of last inventory update
    """

    materials: Dict[str, Material] = field(default_factory=dict)
    current_levels: Dict[str, float] = field(default_factory=dict)
    reserved_quantities: Dict[str, float] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)

    def add_material(self, material: Material, initial_quantity: float = 0.0) -> None:
        """Add a new material to inventory.

        Args:
            material: Material to add
            initial_quantity: Initial quantity in inventory
        """
        if not isinstance(material, Material):
            raise ValidationError("material must be a Material instance")
        if initial_quantity < 0:
            raise ValidationError("initial_quantity must be non-negative")

        self.materials[material.material_id] = material
        self.current_levels[material.material_id] = initial_quantity
        self.reserved_quantities[material.material_id] = 0.0

    def get_available_quantity(self, material_id: str) -> float:
        """Get available quantity of a material.

        Args:
            material_id: ID of the material

        Returns:
            float: Available quantity (current level minus reserved)
        """
        if material_id not in self.materials:
            raise ValidationError(f"Material {material_id} not found")
        return self.current_levels[material_id] - self.reserved_quantities[material_id]

    def reserve_material(self, material_id: str, quantity: float) -> bool:
        """Reserve material for a job.

        Args:
            material_id: ID of the material
            quantity: Quantity to reserve

        Returns:
            bool: True if reservation successful, False otherwise
        """
        if material_id not in self.materials:
            raise ValidationError(f"Material {material_id} not found")
        if quantity <= 0:
            raise ValidationError("quantity must be positive")

        available = self.get_available_quantity(material_id)
        if available >= quantity:
            self.reserved_quantities[material_id] += quantity
            return True
        return False

    def release_material(self, material_id: str, quantity: float) -> None:
        """Release reserved material.

        Args:
            material_id: ID of the material
            quantity: Quantity to release
        """
        if material_id not in self.materials:
            raise ValidationError(f"Material {material_id} not found")
        if quantity <= 0:
            raise ValidationError("quantity must be positive")
        if self.reserved_quantities[material_id] < quantity:
            raise ValidationError("Cannot release more than reserved")

        self.reserved_quantities[material_id] -= quantity

    def update_inventory(self, material_id: str, quantity: float) -> None:
        """Update inventory level for a material.

        Args:
            material_id: ID of the material
            quantity: New quantity to set
        """
        if material_id not in self.materials:
            raise ValidationError(f"Material {material_id} not found")
        if quantity < 0:
            raise ValidationError("quantity must be non-negative")

        material = self.materials[material_id]
        if quantity > material.max_quantity:
            raise ValidationError(f"Quantity exceeds maximum ({material.max_quantity})")

        self.current_levels[material_id] = quantity
        self.last_updated = datetime.now()

    def check_material_availability(self, material_id: str, required_quantity: float) -> bool:
        """Check if required quantity of material is available.

        Args:
            material_id: ID of the material
            required_quantity: Quantity required

        Returns:
            bool: True if material is available, False otherwise
        """
        return self.get_available_quantity(material_id) >= required_quantity

    def get_low_stock_materials(self) -> List[tuple[str, float, float]]:
        """Get list of materials with low stock levels.

        Returns:
            List[tuple[str, float, float]]: List of (material_id, current_level, min_quantity)
        """
        low_stock = []
        for material_id, material in self.materials.items():
            current = self.current_levels[material_id]
            if current <= material.min_quantity:
                low_stock.append((material_id, current, material.min_quantity))
        return low_stock
