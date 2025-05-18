import copy
import json
import logging
import time

import numpy as np
import pandas as pd

from lekin.dashboard.gantt import get_scheduling_res_from_all_jobs, plot_gantt_chart
from lekin.lekin_struct import (
    Job,
    JobCollector,
    Operation,
    OperationCollector,
    Resource,
    ResourceCollector,
    Route,
    RouteCollector,
)
from lekin.solver.meta_heuristics.genetic import GeneticScheduler

logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.DEBUG)


class DataReader(object):
    def __init__(self):
        # 每一个订单O需要的job顺序, 横着看每一行有一个顺序
        machine_sequence_df = pd.read_excel("./data/JSP_dataset.xlsx", sheet_name="Machines Sequence", index_col=[0])
        # 每一个订单O的每一个工序J的所需时间
        processing_time_df = pd.read_excel("./data/JSP_dataset.xlsx", sheet_name="Processing Time", index_col=[0])

        num_jobs = processing_time_df.shape[0]
        num_machines = processing_time_df.shape[1]

        processing_time = [list(map(int, processing_time_df.iloc[i])) for i in range(num_jobs)]
        machine_sequence = [list(map(int, machine_sequence_df.iloc[i])) for i in range(num_jobs)]
        print(processing_time)
        print(machine_sequence)

        num_gene = num_jobs * num_machines  # 基因数量 = job * 机器
        print("Number Gene: ", num_gene)
        population_size = int(30)  # default value is 30
        crossover_rate = float(0.8)  # default value is 0.8
        mutation_rate = float(0.2)  # default value is 0.2
        mutation_selection_rate = float(0.2)
        num_mutation_jobs = round(num_gene * mutation_selection_rate)
        num_iteration = int(2000)  # default value is 2000

        start_time = time.time()

        """==================== main code ==============================="""
        """----- generate initial population -----"""
        Tbest = 999999999999999
        population_list = []
        makespan_record = []
        for i in range(population_size):
            nxm_random_num = list(
                np.random.permutation(num_gene)
            )  # generate a random permutation of 0 to num_job*num_mc-1
            population_list.append(nxm_random_num)  # add to the population_list
            for j in range(num_gene):
                population_list[i][j] = (
                    population_list[i][j] % num_jobs
                )  # convert to job number format, every job appears m times

        for n in range(num_iteration):
            Tbest_now = 99999999999

            """-------- two point crossover --------"""
            parent_list = copy.deepcopy(population_list)
            offspring_list = copy.deepcopy(population_list)
            # 因为每次选择一部分
            S = list(
                np.random.permutation(population_size)
            )  # generate a random sequence to select the parent chromosome to crossover

            for m in range(int(population_size / 2)):
                crossover_prob = np.random.rand()
                if crossover_rate >= crossover_prob:
                    parent_1 = population_list[S[2 * m]][:]
                    parent_2 = population_list[S[2 * m + 1]][:]
                    child_1 = parent_1[:]
                    child_2 = parent_2[:]
                    cutpoint = list(np.random.choice(num_gene, 2, replace=False))
                    cutpoint.sort()

                    # 互换两个染色体，产生新的解. 例子中截取两个基因，在同一位置不同两个染色体上互换
                    child_1[cutpoint[0] : cutpoint[1]] = parent_2[cutpoint[0] : cutpoint[1]]
                    child_2[cutpoint[0] : cutpoint[1]] = parent_1[cutpoint[0] : cutpoint[1]]
                    # 更新到后代中
                    offspring_list[S[2 * m]] = child_1[:]
                    offspring_list[S[2 * m + 1]] = child_2[:]

            """----------repairment-------------"""
            for m in range(population_size):
                job_count = {}
                # 'larger' record jobs appear in the chromosome more than m times, and 'less' records less than m times
                larger, less = (
                    [],
                    [],
                )
                for i in range(num_jobs):
                    if i in offspring_list[m]:
                        count = offspring_list[m].count(i)
                        pos = offspring_list[m].index(i)
                        job_count[i] = [count, pos]  # store the above two values to the job_count dictionary
                    else:
                        count = 0
                        job_count[i] = [count, 0]
                    if count > num_machines:
                        larger.append(i)
                    elif count < num_machines:
                        less.append(i)

                for k in range(len(larger)):
                    chg_job = larger[k]
                    while job_count[chg_job][0] > num_machines:
                        for d in range(len(less)):
                            if job_count[less[d]][0] < num_machines:
                                offspring_list[m][job_count[chg_job][1]] = less[d]
                                job_count[chg_job][1] = offspring_list[m].index(chg_job)
                                job_count[chg_job][0] = job_count[chg_job][0] - 1
                                job_count[less[d]][0] = job_count[less[d]][0] + 1
                            if job_count[chg_job][0] == num_machines:
                                break

            """--------mutation 变异--------"""
            for m in range(len(offspring_list)):
                mutation_prob = np.random.rand()
                if mutation_rate >= mutation_prob:
                    m_chg = list(
                        np.random.choice(num_gene, num_mutation_jobs, replace=False)
                    )  # chooses the position to mutation
                    t_value_last = offspring_list[m][m_chg[0]]  # save the value which is on the first mutation position
                    for i in range(num_mutation_jobs - 1):
                        offspring_list[m][m_chg[i]] = offspring_list[m][m_chg[i + 1]]  # displacement

                    offspring_list[m][
                        m_chg[num_mutation_jobs - 1]
                    ] = t_value_last  # move the value of the first mutation position to the last mutation position

            """--------fitness value(calculate make span)-------------"""
            total_chromosome = copy.deepcopy(parent_list) + copy.deepcopy(
                offspring_list
            )  # parent and offspring chromosomes combination
            chrom_fitness, chrom_fit = [], []
            total_fitness = 0
            for m in range(population_size * 2):
                j_keys = [j for j in range(num_jobs)]
                key_count = {key: 0 for key in j_keys}
                j_count = {key: 0 for key in j_keys}
                m_keys = [j + 1 for j in range(num_machines)]
                m_count = {key: 0 for key in m_keys}

                for i in total_chromosome[m]:
                    gen_t = int(processing_time[i][key_count[i]])
                    gen_m = int(machine_sequence[i][key_count[i]])
                    j_count[i] = j_count[i] + gen_t
                    m_count[gen_m] = m_count[gen_m] + gen_t

                    if m_count[gen_m] < j_count[i]:
                        m_count[gen_m] = j_count[i]
                    elif m_count[gen_m] > j_count[i]:
                        j_count[i] = m_count[gen_m]

                    key_count[i] = key_count[i] + 1

                makespan = max(j_count.values())
                chrom_fitness.append(1 / makespan)
                chrom_fit.append(makespan)
                total_fitness = total_fitness + chrom_fitness[m]

            """----------selection(roulette wheel approach)----------"""
            pk, qk = [], []

            for i in range(population_size * 2):
                pk.append(chrom_fitness[i] / total_fitness)
            for i in range(population_size * 2):
                cumulative = 0
                for j in range(0, i + 1):
                    cumulative = cumulative + pk[j]
                qk.append(cumulative)

            selection_rand = [np.random.rand() for i in range(population_size)]

            for i in range(population_size):
                if selection_rand[i] <= qk[0]:
                    population_list[i] = copy.deepcopy(total_chromosome[0])
                else:
                    for j in range(0, population_size * 2 - 1):
                        if selection_rand[i] > qk[j] and selection_rand[i] <= qk[j + 1]:
                            population_list[i] = copy.deepcopy(total_chromosome[j + 1])
                            break

            """----------comparison----------"""
            for i in range(population_size * 2):
                if chrom_fit[i] < Tbest_now:
                    Tbest_now = chrom_fit[i]
                    sequence_now = copy.deepcopy(total_chromosome[i])
            if Tbest_now <= Tbest:
                Tbest = Tbest_now
                sequence_best = copy.deepcopy(sequence_now)

            makespan_record.append(Tbest)

        """----------result----------"""
        print("optimal sequence", sequence_best)
        print("optimal value:%f" % Tbest)
        print("the elapsed time:%s" % (time.time() - start_time))

    def get_job_collector(self):
        return

    def get_resource_collector(self):
        return


class GeneticOPT(object):
    def __init__(self):
        self.genetic = GeneticScheduler(
            popolation_size=30, crossover_rate=0.8, mutation_rate=0.2, mutation_selection_rate=0.2, num_iterations=2000
        )

    def run(self):
        while True:
            np.random.seed(int(time.time()))


def main():
    data_reader = DataReader()
    print(data_reader)

    # job_collector = data_reader.get_job_collector()
    # resource_collector = data_reader.get_resource_collector()
    #
    # opt = GeneticOPT(job_collector, resource_collector)
    # opt.run()


if __name__ == "__main__":
    main()
