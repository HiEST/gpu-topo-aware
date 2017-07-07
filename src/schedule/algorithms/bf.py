#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# The second queue is used to add the jobs that could not be placed in the current scenario, e.g. load. This queue
# is defined to have priority against the former queue.
#
# Copyright © 2017 Marcelo Amaral <marcelo.amaral@bsc.es>

import copy
import random

random.seed(1234)


def update_resources(job, cluster_resources, mid):
    for jgpu in job.get_alloc_gpus():
        for pgpu in cluster_resources.machines[mid].sockets[jgpu.socket].gpus:
            if jgpu.id == pgpu.id:
                pgpu.allocated = True

    return cluster_resources


def get_jobs(placement, cluster_resources):
    placement = sorted(placement.iteritems(),  key=lambda k: k[1].arrival_time)
    jobs = []
    # TODO: by now we have only one machine, but I need to change it for a cluster
    if cluster_resources.machines[0].get_total_free_gpus() > 0:
        for _, job in placement:
            if job.get_num_gpus() <= cluster_resources.machines[0].get_total_free_gpus():
                jobs.append(job)
            # else:
            #     break
    return jobs


def get_socket_id(machine):
    """Get the socket with less GPUs"""
    socket_id = None
    gpus = 1000
    for socket in machine.sockets:
        sgpu = machine.get_free_gpu_per_socket(socket.id)
        if sgpu > 0:
            if socket_id is None:
                socket_id = socket.id
            if gpus >= sgpu:
                socket_id = socket.id
                gpus = sgpu
    return socket_id


def bf(curr_time, queue1, queue2, cluster_resources, profile, utility):
    temp_resources = copy.deepcopy(cluster_resources)
    placement = dict()
    for _ in range(len(queue2)):
        job = queue2.popleft()
        placement[job.id] = job
    for _ in range(len(queue1)):
        job = queue1.popleft()
        placement[job.id] = job

    jobs = get_jobs(placement, cluster_resources)
    # We use reserve sort to do pop in the first arrived job
    jobs = sorted(jobs,  key=lambda k: k.arrival_time, reverse=True)
    while len(jobs) > 0:
        job = jobs.pop()
        best_placement = None

        for mid, machine in temp_resources.machines.items():
            mem = copy.deepcopy(job.mem)
            task = copy.deepcopy(job.tasks)
            num_gpus = job.get_num_gpus()

            if machine.get_total_free_mem() >= mem and \
                            machine.get_total_free_cores() >= task and \
                            machine.get_total_free_gpus() >= num_gpus:

                # create a solution candidate
                solution = dict()
                solution['machine'] = mid
                solution['arrival_job_time'] = job.arrival_time
                solution['mem_per_socket'] = [0, 0]
                solution['core_per_socket'] = [0, 0]
                solution['gpu_per_socket'] = [[], []]

                # "Randomly" select the socket
                for _ in machine.sockets:
                    socket_id = get_socket_id(machine)
                    if socket_id is not None:
                        if machine.get_free_mem_per_socket(socket_id) >= mem:
                            smem = mem
                        else:
                            smem = machine.get_free_mem_per_socket(socket_id)

                        if machine.get_free_core_per_socket(socket_id) >= task:
                            stask = task
                        else:
                            stask = machine.get_free_core_per_socket(socket_id)

                        if machine.get_free_gpu_per_socket(socket_id) >= num_gpus:
                            sgpu = num_gpus
                        else:
                            sgpu = machine.get_free_gpu_per_socket(socket_id)

                        # First, reduce the machine resources the requested resources
                        machine.alloc_mem_in_socket(socket_id, smem)
                        solution['mem_per_socket'][socket_id] += smem
                        mem -= smem

                        machine.alloc_core_in_socket(socket_id, stask)
                        solution['core_per_socket'][socket_id] += stask
                        task -= stask

                        # Randomly allocate the gpus
                        allocated_gpus = 1
                        for gpu in machine.sockets[socket_id].gpus:
                            if not gpu.allocated:
                                if allocated_gpus <= sgpu:
                                    pair = dict()
                                    pair["hgpu"] = gpu
                                    pair["mid"] = mid
                                    pair["job"] = job
                                    solution['gpu_per_socket'][socket_id].append(pair)
                                    allocated_gpus += 1
                                    gpu.allocated = True
                                else:
                                    break
                        num_gpus -= sgpu

                        # if the job resource was already allocated stop, otherwise allocate resources in other sockets
                        if mem == 0 and task == 0 and num_gpus == 0:
                            break

            if mem == 0 and task == 0 and num_gpus == 0:
                # if there were enough resource in this machine to place the job, save the placement decision
                job.placement.placed = True
                job.placement.start_time = curr_time
                job.placement.end_time = None  # TODO: When the simulator is on, set the time accordingly to the scenario
                job.placement.machine = solution['machine']
                job.placement.mem_per_socket = solution['mem_per_socket']
                job.placement.core_per_socket = solution['core_per_socket']
                job.placement.gpu_per_socket = solution['gpu_per_socket']

                s = dict()
                s['gpus'] = list()
                for socket in solution['gpu_per_socket']:
                    for gpu in socket:
                        s['gpus'].append(gpu['hgpu'])
                s['communication'] = utility.get_comm_cost(s['gpus'], s['gpus'], machine.gpu_distance,
                                                           machine.gpu_distance, None)
                s['interference'] = utility.get_interference_in_job(job, machine, s['gpus'], profile)
                s['fragmentation'] = utility.get_fragmentation(machine, s['gpus'])
                job.placement.costs.comm = s['communication']
                job.placement.costs.suffered_interf = s['interference']
                job.placement.costs.frag = s['fragmentation']
                job.placement.job_utility = utility.calculate_utility(s, system=False)
                job.placement.machine = mid

                # The System Utility also consider the impact of this job will do in the utility of the other running jobs
                # So that, for each running job in the machine, it calculates the average Utility between them
                # The goal is to maximize the minimal utility
                if len(machine.running_jobs) > 0:
                    s['interference_on_other_jobs'] = utility.get_interference_on_other_jobs(job, machine,
                                                                                             s['gpus'], profile)
                    job.placement.costs.suffered_interf = s['interference_on_other_jobs']
                job.placement.system_utility = utility.calculate_utility(s)
                if best_placement is None:
                    best_placement = job
                elif best_placement.placement.job_utility < job.placement.job_utility:
                    best_placement = job

                # break
        if best_placement is not None:
            placement[best_placement.id] = best_placement
            # update the resource allocation
            temp_resources = update_resources(best_placement, temp_resources, best_placement.placement.machine)

    placement = sorted(placement.iteritems(), key=lambda k: k[1].arrival_time, reverse=True)
    placement = [s[1] for s in placement]
    return placement
