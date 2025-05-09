def push_dense(schedule):
    changed = True

    while changed:
        changed = False

        for resource in schedule.resources:
            slots = sorted(resource.slots, key=lambda x: x.start_time)

            for i in range(len(slots) - 1):
                curr_slot = slots[i]
                next_slot = slots[i + 1]

                if curr_slot.end_time < next_slot.start_time:
                    # Gap exists between operations

                    gap = next_slot.start_time - curr_slot.end_time

                    if next_slot.operation.can_start_early(gap):
                        # Update slots
                        next_slot.start_time -= gap
                        next_slot.end_time -= gap

                        curr_slot.end_time = next_slot.start_time

                        changed = True

    return schedule
