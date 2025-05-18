import argparse
import json
import logging

from lekin.dashboard.gantt import get_scheduling_res_from_all_jobs, plot_gantt_chart
from lekin.lekin_struct import Job, JobCollector, Operation, Resource, ResourceCollector, Route, RouteCollector
from lekin.solver.construction_heuristics import BackwardScheduler, ForwardScheduler

logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.DEBUG)


def prepare_data(file_path="./data/k1.json"):
    with open(file_path, "r", encoding="utf8") as file:  # read file from path
        data = json.loads(file.read())

    job_collector = JobCollector()
    route_collector = RouteCollector()
    resource_collector = ResourceCollector()

    if list(data.keys()) == ["itineraries", "machines"]:
        resources = data["machines"]  # is first level structure is correct, then split
        routes = data["itineraries"]

        # parse the resource
        for re in resources:
            re_name = re["machineName"]
            re_id = int(re_name.replace("M", ""))
            resource = Resource(resource_id=re_id, resource_name=re_name)
            resource.available_hours = list(range(1, 200))
            resource_collector.add_resource_dict(resource)

        print([i.resource_id for i in resource_collector.get_all_resources()])
        print(resource_collector.get_all_resources()[0].available_hours)

        # parse the job and route
        for ro in routes:
            ro_id = int(ro["itineraryName"].replace("Itinerary ", ""))
            route = Route(route_id=ro_id)
            operations_sequence = []
            for ta in ro["tasksList"]:
                op_name = ta["taskName"]
                op_id = ta["taskName"].replace("Task ", "")
                op_pt = ta["taskDuration"]

                op_tm = []
                if isinstance(ta["taskMachine"], list):
                    for re in ta["taskMachine"]:
                        re_name = re["machineName"]
                        re_id = int(re_name.replace("M", ""))
                        op_tm.append(resource_collector.get_resource_by_id(re_id))
                else:
                    re_name = ta["taskMachine"]["machineName"]
                    re_id = int(re_name.replace("M", ""))
                    op_tm.append(resource_collector.get_resource_by_id(re_id))

                operations_sequence.append(
                    Operation(
                        operation_id=op_id,
                        operation_name=op_name,
                        quantity=1,
                        processing_time=op_pt,
                        parent_job_id=ro_id,  # route defines job here
                        available_resource=op_tm,
                    )
                )

            route.operations_sequence = operations_sequence
            route_collector.add_route(route)

            job_collector.add_job(Job(job_id=ro_id, assigned_route_id=ro_id))

        # print(resources)
        # print(routes)
    return job_collector, resource_collector, route_collector


def run_scheduling(job_collector, resource_collector, route_collector, use_model="forward"):
    if use_model == "forward":
        scheduler = ForwardScheduler(job_collector, resource_collector, route_collector)
    elif use_model == "backward":
        scheduler = BackwardScheduler(job_collector, resource_collector, route_collector)
    else:
        raise ValueError

    scheduler.run()
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--use_model", type=str, default="backward")
    args = parser.parse_args()

    job_collector, resource_collector, route_collector = prepare_data(file_path="./data/k1.json")
    run_scheduling(job_collector, resource_collector, route_collector, use_model=args.use_model)

    scheduling_res = get_scheduling_res_from_all_jobs(job_collector)
    print(scheduling_res)
    plot_gantt_chart(job_collector, scheduling_res)
