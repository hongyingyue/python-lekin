"""
Lekin - A Flexible Job Shop Scheduling Problem (FJSP) Framework

This module provides the core data structures for modeling and solving Job Shop Scheduling Problems.
The framework is designed to be flexible, extensible, and easy to use for both research and practical applications.

Core Concepts:
- Job: Represents a manufacturing order or production task
- Operation: Represents a specific manufacturing step within a job
- Resource: Represents machines, workstations, or other processing units
- Route: Defines the sequence of operations for a job
- TimeSlot: Represents available time slots for scheduling

Example:
    >>> from lekin.lekin_struct import Job, Operation, Resource
    >>> job = Job("J1", priority=1, quantity=100)
    >>> operation = Operation("O1", duration=30)
    >>> resource = Resource("M1", capacity=1)
"""

from lekin.lekin_struct.job import Job, JobCollector
from lekin.lekin_struct.operation import Operation, OperationCollector
from lekin.lekin_struct.resource import Resource, ResourceCollector
from lekin.lekin_struct.route import Route, RouteCollector
from lekin.lekin_struct.timeslot import TimeSlot

__version__ = "0.1.0"
__author__ = "Lekin Contributors"
__license__ = "MIT"

__all__ = [
    "Job",
    "JobCollector",
    "Operation",
    "OperationCollector",
    "Resource",
    "ResourceCollector",
    "Route",
    "RouteCollector",
    "TimeSlot",
]
