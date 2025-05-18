"""Tardiness total/maximum/weighted"""


def calculate_tardiness(schedule_result, job):
    end_time = schedule_result[job.route.operations[-1]][1]
    return max(0, end_time - job.demand_date)


def calculate_total_tardiness(schedule_result, jobs):
    total_tardiness = 0
    for job in jobs:
        total_tardiness += calculate_tardiness(schedule_result, job)
    return total_tardiness


def calculate_total_late_jobs(schedule_result, jobs):
    total_late_jobs = 0
    for job in jobs:
        if calculate_tardiness(schedule_result, job) > 0:
            total_late_jobs += 1
    return total_late_jobs


def calculate_total_late_time(schedule_result, jobs):
    total_late_time = 0
    for job in jobs:
        tardiness = calculate_tardiness(schedule_result, job)
        if tardiness > 0:
            total_late_time += tardiness
    return total_late_time
