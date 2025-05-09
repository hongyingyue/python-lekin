def calculate_makespan(job_collector):
    for job in job_collector.job_list:
        op = job.operations
        job.makespan = op.assigned_hours[-1]

        if job.demand_date is not None:
            job.tardiness = job.makespan - job.demand_date
    return


def calculate_changeover_time(schedule_result, job_collector):
    changeover_time = 0
    for resource in job_collector.resources:
        previous_end_time = 0
        for operation in schedule_result:
            if operation.resource == resource:
                changeover_time += max(0, operation.start_time - previous_end_time)
                previous_end_time = operation.end_time
    return changeover_time
