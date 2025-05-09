"""
Operation Struct
op: 单个工单或新增需求的某一道工序
GroupOP: 单个需求或多个需求必须在一起的一道工序
MaterialOP: 同一物料多个需求的一道工序
"""

from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple, Union

if TYPE_CHECKING:
    from .allocation import Allocation
    from .execution_mode import ExecutionMode


class Operation:
    def __init__(
        self,
        operation_id: str,
        operation_name: str,
        quantity: int,
        processing_time: Union[int, List[int], float, List[float]],
        pre_time: float = 0,  # setup times
        post_time: float = 0,
        lead_time: float = 0,
        lag_time: float = 0,
        route_constraint=None,
        available_resource=None,
        available_resource_priority=None,
        parent_job_id=None,
        prev_operation_ids=None,
        next_operation_ids=None,
        **kwargs,
    ):
        self.operation_id = operation_id
        self.operation_name = operation_name
        self.quantity = quantity
        self.processing_time = processing_time
        self.pre_time = pre_time
        self.post_time = post_time
        self.lead_time = lead_time
        self.lag_time = lag_time
        self.route_constraint = route_constraint
        self.available_resource = available_resource
        self.available_resource_priority = available_resource_priority
        self.parent_job_id = parent_job_id
        self.prev_operation_ids = prev_operation_ids  # predecessors
        self.next_operation_ids = next_operation_ids  # successors

        self.earliest_start_time = None
        self.latest_start_time = None
        self.earliest_end_time = None
        self.latest_end_time = None

        self.statue = "none"  # none -> waiting -> pending -> done
        self.assigned_resource = None  # Track the assigned resource
        self.assigned_time_slot = None  # Track the assigned time slot

        self.execution_modes: List["ExecutionMode"] = []
        self.allocations: List["Allocation"] = []

        for key, value in kwargs.items():
            setattr(self, key, value)

    # Add a method to calculate granularity metric based on processing time and available time slot
    def calculate_granularity_metric(self, available_time_slot):
        # Calculate the granularity metric based on processing time and available time slot
        pass

    def is_finished(self):
        return self.assigned_resource is not None

    def add_execution_mode(self, mode: "ExecutionMode"):
        self.execution_modes.append(mode)

    def add_allocation(self, allocation: "Allocation"):
        self.allocations.append(allocation)

    def __repr__(self):
        return f"Operation(id={self.operation_id}, name={self.operation_name})"

    def __str__(self):
        return f"{self.operation_id}-{self.operation_name}"


class JobOperations(object):
    """Operations from same job"""

    def __init__(self, operation_list):
        pass

    @property
    def job(self):
        return


class MaterialOperation(object):
    """
    排产时, MaterialOperation, JobOperation, Operation是三层抽象结构
    resource.assigned_material_op = list[MaterialOperation]
    """

    def __init__(self, job_operation_list):
        pass

    @property
    def material(self):
        return


class OperationCollector:
    def __init__(self):
        self.operation_list = []  # List to store Operation objects

    def add_operation(self, operation):
        self.operation_list.append(operation)

    def get_operation_by_id(self, operation_id):
        for operation in self.operation_list:
            if operation.operation_id == operation_id:
                return operation
        return None

    def get_operations_by_job_and_route(self, job_list, route_list):
        assert len(job_list) == len(route_list)

        for job, route in zip(job_list, route_list):
            # Get the operations for the current job and route
            # route = route_list[route_index]
            job_operations = route.get_operations()

            # Fill in the job_id for each operation
            for i, operation in enumerate(job_operations):
                if i > 0:
                    operation.parent_operation_id = job_operations[i - 1].operation_id
                if i < len(job_operations) - 1:
                    operation.next_operation_id = job_operations[i + 1].operation_id

                operation.job_id = job.job_id

                # Extend the list of all operations with the current job's operations
                self.operation_list.extend(job_operations)

                # Assign the operations to the current job
                job.operations = job_operations
        return self.operation_list

    # def get_operations_by_job_and_route(self, job_list, route_list):
    #     assert len(job_list) == len(route_list)
    #     operation_list = []
    #     for operation in self.operations:
    #         if operation.parent_operation_id is None and operation.route_id == route_id:
    #             # If the operation is the first operation in the route
    #             current_operation = operation
    #             while current_operation:
    #                 if current_operation.job_id == job_id:
    #                     job_operations.append(current_operation)
    #                 next_operation_id = current_operation.next_operation_id
    #                 current_operation = next(
    #                     (op for op in self.operations if op.operation_id == next_operation_id), None
    #                 )
    #     return job_operations
