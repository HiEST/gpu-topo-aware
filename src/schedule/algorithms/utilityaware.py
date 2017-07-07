#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# The second queue is used to add the jobs that could not be placed in the current scenario, e.g. load. This queue
# is defined to have priority against the former queue.
#
# Copyright © 2017 Marcelo Amaral <marcelo.amaral@bsc.es>

import copy
import itertools

from collections import OrderedDict

utility = None
profile = None


# Delete all GPU from P that were not deleted before until the max count half
def delete_gpus(P, half, keep_gpus):
    deleted_gpus = list()

    # Sort the sockets with less available GPUs
    sockets = dict()
    for so in P.sockets:
        sockets[so] = len(so.gpus)

    # First delete the allocated GPUs
    total_gpus = P.get_total_num_gpus()
    for resource, _ in sockets.iteritems():
        if len(resource.gpus) > 0:
            gpu = resource.gpus.pop(0)
            if not gpu.allocated:
                resource.gpus.append(gpu)
                continue

            del P.gpu_distance[gpu.id]
            deleted_gpus.append(gpu.id)
            total_gpus -= 1

    # Sort the candidate to delete by the lower number of gpus. It attempts to keep the partition as higher as possible
    sockets = OrderedDict(sorted(sockets.items(), key=lambda t: t[1], reverse=False))

    for resource, _ in sockets.iteritems():
        if total_gpus <= half:
            break

        gpu_per_socket = len(resource.gpus)
        for _ in range(gpu_per_socket):
            if total_gpus <= half:
                break
            if len(resource.gpus) > 0:
                gpu = resource.gpus.pop(0)
                if gpu.id in keep_gpus:
                    resource.gpus.append(gpu)
                    continue

                del P.gpu_distance[gpu.id]
                deleted_gpus.append(gpu.id)
                total_gpus -= 1

    return P, deleted_gpus


def delete_machines(P, machine_list):
    ids = list()
    for id, _ in P.machines.iteritems():
        ids.append(id)

    for id in ids:
        if id in machine_list:
            del P.machines[id]
    return P


def is_in_partition(glist, machine):
    if machine is None:
        return False

    for gpu1 in glist:
        for gpu2 in machine.get_free_gpus():
            if gpu1.id == gpu2.id:
                return True
    return False


def get_machine_best_placement(A, gpu_list, P0, P1, C, external_cost):
    solutions = list()

    # Calculate the jobs preference in each partition
    for glist in list(itertools.combinations(gpu_list, A.get_num_gpus())):
        s = dict()
        s['gpus'] = list()
        for gpu in glist:
            s['gpus'].append(gpu)

        s['interference'] = 0
        s['fragmentation'] = 0
        s['communication'] = 0
        p0_cost = False
        if is_in_partition(glist, P0):
            s['communication'] += utility.get_comm_cost(glist, gpu_list, P0.gpu_distance, C, external_cost)
            s['interference'] += utility.get_interference_in_job(A, P0, glist, profile)
            s['fragmentation'] += utility.get_fragmentation(P0, glist)
            p0_cost = True

        if P1 is not None:
            if is_in_partition(glist, P1):
                s['communication'] += utility.get_comm_cost(glist, gpu_list, P1.gpu_distance, C, external_cost)
                s['interference'] += utility.get_interference_in_job(A, P1, glist, profile)
                s['fragmentation'] += utility.get_fragmentation(P1, glist)
                if p0_cost:
                    s['interference'] /= 2
                    s['fragmentation'] /= 2

        s['job_utility'] = utility.calculate_utility(s, system=False)

        # The System Utility also consider the impact of this job will do in the utility of the other running jobs
        # So that, for each running job in the machine, it calculates the average Utility between them
        # The goal is to maximize the minimal utility
        if len(P0.running_jobs) > 0:
            s['interference_on_other_jobs'] = utility.get_interference_on_other_jobs(A, P0, glist, profile)
        s['sys_utility'] = utility.calculate_utility(s)

        solutions.append(s)

    # It ordered in reverse ordered_jobs because it will pop the last item, which must be the one with higher utility
    return sorted(solutions, key=lambda t: t['sys_utility'], reverse=False).pop()


def update_job_info(A, solution, mid):
    if A.placement.costs.comm is None:
        A.placement.costs.comm = solution['communication']
        A.placement.costs.suffered_interf = solution['interference']
        if 'interference_on_other_jobs' in solution:
            A.placement.costs.caused_interf = solution['interference']
        A.placement.costs.frag = solution['fragmentation']
        A.placement.system_utility = solution['sys_utility']
        A.placement.job_utility = solution['job_utility']
        A.placement.machine = mid
    return A


def job_graph_partitioning(A, P0, P1, C, external_cost):
    """
      First verify if the application needs to be partitioned over P0 and P1, allocating more applications GPUs into the
       partition that has more available GPUs.
    """
    global profile
    best = None
    solutionsP0 = list()
    solutionsP1 = list()
    A0 = copy.deepcopy(A)
    A1 = copy.deepcopy(A)

    num0, machine_ids0 = get_num_machines_free_gpus(P0)
    num1, machine_ids1 = get_num_machines_free_gpus(P1)

    if len(machine_ids0) <= 0:
        A1 = copy.deepcopy(A)
        A0 = copy.deepcopy(A)
        A0.gpus = list()  # remove GPUs from be placed in partition 0
        return A0, A1, C, False

    if len(machine_ids1) <= 0:
        A0 = copy.deepcopy(A)
        A1 = copy.deepcopy(A)
        A1.gpus = list()  # remove GPUs from be placed in partition 0
        return A0, A1, C, False

    mid0 = machine_ids0[0]
    mid1 = machine_ids1[0]

    if (num0 == 1 and num1 == 1) and (mid0 == mid1):  # If both partitions have the same machine
        if P0.get_num_free_gpus() + P1.get_num_free_gpus() >= len(A.gpus):
            machineP0 = P0.machines[mid0]
            machineP1 = P1.machines[mid1]

            gpu_list = machineP0.get_free_gpus() + machineP1.get_free_gpus()
            solution = get_machine_best_placement(A, gpu_list, machineP0, machineP1, C, external_cost)

            A = update_job_info(A, solution, mid0)
            A0 = copy.deepcopy(A)
            A1 = copy.deepcopy(A)

            for ag in A.gpus:
                hg = solution['gpus'].pop()
                if is_in_partition([hg], machineP0):  # if the alloc gpu is in P0, remove the gpu from the A1
                    A1.gpus.remove(ag)
                else:
                    A0.gpus.remove(ag)

            return A0, A1, C, True

    # If both partitions have different machine
    else:
        solutionsP0 = list()
        bestP0 = dict()
        bestP0['sys_utility'] = -1
        for mid in machine_ids0:
            machineP0 = P0.machines[mid]
            gpu_list = machineP0.get_free_gpus()
            if len(gpu_list) >= len(A.gpus):
                s = get_machine_best_placement(A, gpu_list, machineP0, None, C, external_cost)
                s['mid'] = mid
                s['comm'] = machineP0.get_comm_matrix()
                solutionsP0.append(s)
        if len(solutionsP0) > 0:
            bestP0 = sorted(solutionsP0, key=lambda t: t['sys_utility'], reverse=False).pop()

        solutionsP1 = list()
        bestP1 = dict()
        bestP1['sys_utility'] = -1
        for mid in machine_ids1:
            machineP1 = P1.machines[mid]
            gpu_list = machineP1.get_free_gpus()
            if len(gpu_list) >= len(A.gpus):
                s = get_machine_best_placement(A, gpu_list, machineP1, None, C, external_cost)
                s['mid'] = mid
                s['comm'] = machineP1.get_comm_matrix()
                solutionsP1.append(s)
        if len(solutionsP1) > 0:
            bestP1 = sorted(solutionsP1, key=lambda t: t['sys_utility'], reverse=False).pop()

        if (bestP0['sys_utility'] > -1) and ((bestP0['sys_utility'] > bestP1['sys_utility']) or
                                                 (bestP1['sys_utility'] == -1)):
            A = update_job_info(A, bestP0, bestP0['mid'])
            A0 = copy.deepcopy(A)
            A1 = copy.deepcopy(A)
            A1.gpus = list()  # remove GPUs from be placed in partition 1
            # the communication cost is only update for a higher level to have information of all levels
            if C is None:
                C = bestP0['comm']
            return A0, A1, C, False
        else:
            A = update_job_info(A, bestP1, bestP1['mid'])
            A0 = copy.deepcopy(A)
            A1 = copy.deepcopy(A)
            A0.gpus = list()  # remove GPUs from be placed in partition 0
            # the communication cost is only update for a higher level to have information of all levels
            if C is None:
                C = bestP1['comm']
            return A0, A1, C, False


def get_num_machines_free_gpus(P):
    machine_ids = list()
    num = 0
    for mid, machines in P.machines.iteritems():
        if len(machines.get_free_gpus()) > 0:
            machine_ids.append(mid)
            num += 1
    return num, machine_ids


def physical_graph_partitioning(P):
    P0 = copy.deepcopy(P)
    P1 = copy.deepcopy(P)

    num, machine_ids = get_num_machines_free_gpus(P)

    if num > 1:
        P0_machines = list()
        P1_machines = list()

        half0 = 0
        half1 = 0
        for mid in machine_ids:
            current_gpus = len(P.machines[mid].get_free_gpus())
            if half0 + current_gpus <= half1 + current_gpus:
                P0_machines.append(mid)
                half0 += current_gpus
            else:
                P1_machines.append(mid)
                half1 += current_gpus

        P0 = delete_machines(P0, P1_machines)
        P1 = delete_machines(P1, P0_machines)

    else:
        mid = machine_ids.pop()
        machine = P0.machines[mid]
        total_free_gpus = len(machine.get_free_gpus())

        half1 = total_free_gpus / 2
        half0 = total_free_gpus - half1  # the first partition will be bigger with odd number of gpus

        machineP0, keep_gpus = delete_gpus(machine, half0, [])
        P0.machines[mid] = machineP0

        machine = P1.machines[mid]
        machineP1, _ = delete_gpus(machine, half1, keep_gpus)
        P1.machines[mid] = machineP1
    return P0, P1


# This method is an implementation of the algorithm Hierarchical Static Mapping Dual Recursive Bi-Partitioning
def rdb_mapping(A, P, C, external_cost=False):
    # recursion stop criteria
    if A.get_num_gpus() == 0 or P.get_num_free_gpus() == 0:
        return []

    if P.get_num_free_gpus() == 1:
        for mid, machine in P.machines.iteritems():
            for socket in machine.sockets:
                if machine.get_total_free_gpus_in_socket(socket.id) > 0:
                    hg = machine.sockets[socket.id].gpus.pop()
                    pair = dict()
                    pair["hgpu"] = hg
                    pair["mid"] = mid
                    return [pair]

    # 'graph' partitioning
    P0, P1 = physical_graph_partitioning(P)
    A0, A1, C, external_cost = job_graph_partitioning(A, P0, P1, C, external_cost)

    glist0 = rdb_mapping(A0, P0, C, external_cost)
    glist1 = rdb_mapping(A1, P1, C, external_cost)

    # create the list to return
    pairs = []
    if not glist0 == None:
        for item in glist0:
            pairs.append(item)
    if not glist1 == None:
        for item in glist1:
            pairs.append(item)

    return pairs


# This method is wrapper in the DRB recursion, to create the solution in the right format
def rdb(A, P, curr_time, postpone):
    num_alloc_gpus = 0
    a = copy.deepcopy(A)
    p = copy.deepcopy(P)
    alloc_gpus = [list() for _ in range(2)]

    if A.get_num_gpus() > P.get_max_free_gpus_per_machine():
        return A

    mapping = rdb_mapping(a, p, None)

    # convert the mapping into an array listing the allocated gpus
    glist = list()
    mid = None
    for pair in mapping:
        mid = pair['mid']
        hgpu = pair['hgpu']
        alloc_gpus[hgpu.socket].append(pair)
        glist.append(hgpu)
        num_alloc_gpus += 1

    machine = P.machines[mid]
    # if there were enough resource in this machine to place the job, save the placement decision
    if num_alloc_gpus <= len(machine.get_free_gpus()):
        a = copy.deepcopy(A)
        if num_alloc_gpus == a.get_num_gpus():
            a.placement.machine = mid
            a.placement.placed = True
            a.placement.start_time = curr_time
            a.placement.end_time = None  # TODO: When the simulator is on, set the time accordingly to the scenario
            # TODO: it is allocating memory and cpu in socket 0, but it should allocate where the gpus are
            a.placement.mem_per_socket = [a.mem, 0]
            a.placement.core_per_socket = [a.tasks, 0]
            a.placement.gpu_per_socket = alloc_gpus

            s = dict()
            s['gpus'] = glist
            s['communication'] = utility.get_comm_cost(glist, glist, machine.gpu_distance, machine.gpu_distance)
            s['interference'] = utility.get_interference_in_job(A, machine, glist, profile)
            s['fragmentation'] = utility.get_fragmentation(machine, glist)
            a.placement.costs.comm = s['communication']
            a.placement.costs.suffered_interf = s['interference']
            a.placement.costs.frag = s['fragmentation']
            a.placement.job_utility = utility.calculate_utility(s, system=False)
            # The System Utility also consider the impact of this job will do in the utility of the other running jobs
            # So that, for each running job in the machine, it calculates the average Utility between them
            # The goal is to maximize the minimal utility
            if len(machine.running_jobs) > 0:
                s['interference_on_other_jobs'] = utility.get_interference_on_other_jobs(A, machine, glist, profile)
                a.placement.costs.caused_interf = s['interference_on_other_jobs']
            if a.placement.costs.caused_interf is None:
                a.placement.costs.caused_interf = 0.01
            a.placement.system_utility = utility.calculate_utility(s)

        if postpone:
            # print a.placement.system_utility, a.minimal_utility
            if a.placement.job_utility >= a.minimal_utility:
                return a
        else:
            return a
    return A


def filter_available_resources(P):
    for mid, machine in P.machines.items():
        for resource in machine.sockets:
            gpu_per_socket = len(resource.gpus)
            for _ in range(gpu_per_socket):
                gpu = resource.gpus.pop(0)
                if not gpu.allocated:
                    resource.gpus.append(gpu)

    return P


def update_resources(job, cluster_resources, mid):
    cluster_resources.machines[mid].running_jobs[job.id] = job
    for jgpu in job.get_alloc_gpus():
        for pgpu in cluster_resources.machines[mid].sockets[jgpu.socket].gpus:
            if jgpu.id == pgpu.id:
                pgpu.allocated = True

    return cluster_resources


def get_jobs(queue2, queue1, cluster_resources):
        jobs = []
        # TODO: by now we have only one machine, but I need to change it for a cluster
        for _ in range(len(queue2)):
            job = queue2.popleft()
            if job.get_num_gpus() <= cluster_resources.machines[0].get_total_free_gpus():
                jobs.append(job)
            else:
                queue2.append(job)

        for _, machine in cluster_resources.machines.iteritems():
            if machine.get_total_free_gpus() > 0:
                for _ in range(len(queue1)):
                    job = queue1.popleft()
                    if job.get_num_gpus() <= machine.get_total_free_gpus():
                        jobs.append(job)
                    else:
                        queue1.append(job)
        return jobs


def utilityaware(curtime, queue2, queue1, cluster_resources, job_profile, obj_utility, postpone):
    """
        First it loads the scheduler configurations.
        It use global variables here to use less memory in the recursion steps.
        Then, for each job it calculates its utility within each machine.
    """
    jobs = get_jobs(queue2, queue1, cluster_resources)
    global utility
    global profile
    utility = obj_utility
    profile = job_profile

    tmp_resources = filter_available_resources(copy.deepcopy(cluster_resources))
    placement = list()

    for job in jobs:
        job.placement.placed = False
        job.placement.utility = 0

        if job.get_num_gpus() <= tmp_resources.get_num_free_gpus():
            s = rdb(job, tmp_resources, curtime, postpone)
        else:
            s = job

        if s.placement.placed:
            placement.append(s)
            tmp_resources = update_resources(s, tmp_resources, s.placement.machine)
        else:
            job.placement.placed = False
            placement.append(job)

    return placement


if __name__ == "__main__":
    pass
