# push dense
# for i, (id, resource) in enumerate(resource_collector.resources_dict.items()):
#     logging.info(
#         f'Start to push {i + 1}/{len(resource_collector.resources_dict)} resources'
#     )
#     assigned_ops = resource.assigned_operations
#     assigned_ops.sort()
#     for op in assigned_ops:
#         buffer_push = op.buffer
#         if buffer_push > resource.available_capacity:
#             buffer_push = resource.available_capacity

#         op.start_time -= buffer_push

# # last chance for remaining jobs
# for job in self.unassigned_jobs:
#     logging.warning(f'Abnornal! No scheduling for job {job.job_id}')
