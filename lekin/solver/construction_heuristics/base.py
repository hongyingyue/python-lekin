import logging


class BaseScheduler(object):
    def __init__(self, job_collector, resource_collector, **kwargs):
        self.job_collector = job_collector
        self.resource_collector = resource_collector

        for key, value in kwargs.items():
            setattr(self, key, value)

    def run(self):
        raise NotImplementedError

    def scheduling_job(self, job, **kwargs):
        raise NotImplementedError

    def find_best_resource_and_timeslot_for_operation(self, operation, **kwargs):
        raise NotImplementedError
