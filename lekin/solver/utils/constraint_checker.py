"""
Constraint checking for scheduling solutions.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ConstraintChecker:
    """Validates scheduling solutions against various constraints."""

    def validate_solution(self, solution: Dict[str, Any]) -> bool:
        """Validate if a solution meets all constraints.

        Args:
            solution: The solution to validate

        Returns:
            True if solution is valid, False otherwise
        """
        try:
            return all(
                [
                    self._check_resource_capacity(solution),
                    self._check_operation_sequence(solution),
                    self._check_time_windows(solution),
                    self._check_resource_compatibility(solution),
                    self._check_precedence_constraints(solution),
                ]
            )
        except Exception as e:
            logger.error(f"Error validating solution: {str(e)}")
            return False

    def _check_resource_capacity(self, solution: Dict[str, Any]) -> bool:
        """Check if resource capacity constraints are satisfied.

        Args:
            solution: The solution to check

        Returns:
            True if resource capacity constraints are satisfied, False otherwise
        """
        try:
            for resource_id, operations in solution["resource_assignments"].items():
                # Get all time slots for this resource
                resource_slots = []
                for op in operations:
                    op_data = next((o for o in solution["scheduled_operations"] if o["operation_id"] == op), None)
                    if op_data:
                        resource_slots.append({"start": op_data["start_time"], "end": op_data["end_time"]})

                # Check for overlaps
                for i in range(len(resource_slots)):
                    for j in range(i + 1, len(resource_slots)):
                        if (
                            resource_slots[i]["start"] < resource_slots[j]["end"]
                            and resource_slots[i]["end"] > resource_slots[j]["start"]
                        ):
                            logger.warning(f"Resource {resource_id} has overlapping operations")
                            return False

            return True

        except Exception as e:
            logger.error(f"Error checking resource capacity: {str(e)}")
            return False

    def _check_operation_sequence(self, solution: Dict[str, Any]) -> bool:
        """Check if operation sequence constraints are satisfied.

        Args:
            solution: The solution to check

        Returns:
            True if operation sequence constraints are satisfied, False otherwise
        """
        try:
            # Group operations by job
            job_operations = {}
            for op in solution["scheduled_operations"]:
                job_id = op["job_id"]
                if job_id not in job_operations:
                    job_operations[job_id] = []
                job_operations[job_id].append(op)

            # Check sequence for each job
            for job_id, operations in job_operations.items():
                # Sort by start time
                operations.sort(key=lambda x: x["start_time"])

                # Check if operations are in correct sequence
                for i in range(len(operations) - 1):
                    if operations[i]["end_time"] > operations[i + 1]["start_time"]:
                        logger.warning(f"Job {job_id} has operations out of sequence")
                        return False

            return True

        except Exception as e:
            logger.error(f"Error checking operation sequence: {str(e)}")
            return False

    def _check_time_windows(self, solution: Dict[str, Any]) -> bool:
        """Check if time window constraints are satisfied.

        Args:
            solution: The solution to check

        Returns:
            True if time window constraints are satisfied, False otherwise
        """
        try:
            for op in solution["scheduled_operations"]:
                # Check if operation is within allowed time window
                if not self._is_within_time_window(op):
                    logger.warning(f"Operation {op['operation_id']} is outside time window")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error checking time windows: {str(e)}")
            return False

    def _check_resource_compatibility(self, solution: Dict[str, Any]) -> bool:
        """Check if resource compatibility constraints are satisfied.

        Args:
            solution: The solution to check

        Returns:
            True if resource compatibility constraints are satisfied, False otherwise
        """
        try:
            for op in solution["scheduled_operations"]:
                # Check if assigned resource is compatible with operation
                if not self._is_resource_compatible(op):
                    logger.warning(f"Operation {op['operation_id']} assigned to incompatible resource")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error checking resource compatibility: {str(e)}")
            return False

    def _check_precedence_constraints(self, solution: Dict[str, Any]) -> bool:
        """Check if precedence constraints are satisfied.

        Args:
            solution: The solution to check

        Returns:
            True if precedence constraints are satisfied, False otherwise
        """
        try:
            # Group operations by job
            job_operations = {}
            for op in solution["scheduled_operations"]:
                job_id = op["job_id"]
                if job_id not in job_operations:
                    job_operations[job_id] = []
                job_operations[job_id].append(op)

            # Check precedence for each job
            for job_id, operations in job_operations.items():
                # Sort by sequence number
                operations.sort(key=lambda x: x.get("sequence_number", 0))

                # Check if operations respect precedence
                for i in range(len(operations) - 1):
                    if operations[i]["end_time"] > operations[i + 1]["start_time"]:
                        logger.warning(f"Job {job_id} has precedence violation")
                        return False

            return True

        except Exception as e:
            logger.error(f"Error checking precedence constraints: {str(e)}")
            return False

    def _is_within_time_window(self, operation: Dict[str, Any]) -> bool:
        """Check if an operation is within its allowed time window.

        Args:
            operation: The operation to check

        Returns:
            True if operation is within time window, False otherwise
        """
        # Implement your time window checking logic here
        return True  # Placeholder

    def _is_resource_compatible(self, operation: Dict[str, Any]) -> bool:
        """Check if an operation is assigned to a compatible resource.

        Args:
            operation: The operation to check

        Returns:
            True if resource is compatible, False otherwise
        """
        # Implement your resource compatibility checking logic here
        return True  # Placeholder
