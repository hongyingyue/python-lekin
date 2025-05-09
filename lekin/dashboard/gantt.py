"""
Gantt
"""

import logging
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple, Type, Union

from matplotlib import ticker
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import pandas as pd

logging.getLogger("matplotlib.font_manager").disabled = True


def get_scheduling_res_from_all_jobs(job_collector):
    ops = []
    for job in job_collector.job_list:
        ops += job.operations

    scheduling_res = []
    for op in ops:
        scheduling_res.append(
            [
                op.operation_id,
                op.parent_job_id,
                op.quantity,
                op.assigned_resource.resource_id,
                min(op.assigned_hours),
                max(op.assigned_hours),
            ]
        )
    scheduling_res = pd.DataFrame(scheduling_res, columns=["Operation", "Job", "Quantity", "Resource", "Start", "End"])
    scheduling_res["Duration"] = scheduling_res["End"] - scheduling_res["Start"]  # + 1
    return scheduling_res


def plot_gantt_chart(job_collector, scheduling_res):
    color_dict = job_collector.generate_color_list_for_jobs()

    # gantt
    resource_list = []
    for resource, group in scheduling_res.groupby("Resource"):
        resource_list.append(resource)
        start_tuple = []
        color_tuple = []
        for _, op in group.iterrows():
            start_tuple.append(op[["Start", "Duration"]].tolist())
            color_tuple.append(color_dict.get(op["Job"]))

        plt.gca().broken_barh(start_tuple, ((resource + 1) * 10, 9), facecolors=color_tuple)

    # legend
    legends_colors = []
    for job in job_collector.job_list:
        legends_colors.append(patches.Patch(color=color_dict.get(job.job_id), label=f"job{job.job_id}"))
    plt.legend(handles=legends_colors, fontsize=8)

    # resource tick
    resources = resource_list  # list(reversed(resource_list))
    resource_ticks = [15]
    for i in range(len(resources)):
        resource_ticks.append(resource_ticks[i] + 10)  # machine increase + 10
    plt.yticks(resource_ticks[1:], resources)

    plt.grid(True)
    plt.xlabel("Time")
    plt.ylabel("Resources")
    plt.title("Gantt Chart - Scheduling Result")
    plt.show()
