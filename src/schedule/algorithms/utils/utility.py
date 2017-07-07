#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# The second queue is used to add the jobs that could not be placed in the current scenario, e.g. load. This queue
# is defined to have priority against the former queue.
#
# Copyright © 2017 Marcelo Amaral <marcelo.amaral@bsc.es>
import json
import itertools


class Utility:
    def __init__(self, config):
        self.MIN_COST = json.loads(config.get("scheduler", "min_cost"))
        self.policy = dict()

        policy_name = json.loads(config.get("scheduler", "policy"))
        self.policy['weight'] = dict()
        metrics = str(json.loads(config.get("scheduler", "metrics"))).strip()
        metrics = metrics.split(",")
        for metric in metrics:
            metric = str(metric.strip())
            self.policy['weight'][metric] = json.loads(config.get(policy_name, metric))

        lengh = len(self.policy['weight'])
        total_sys = (lengh * (self.MIN_COST ** (1.0 / lengh)))
        self.MAX_SYS_UTILITY = 1 / total_sys
        lengh -= 1
        total_job = (lengh * (self.MIN_COST ** (1.0/lengh)))
        self.MAX_JOB_UTILITY = 1 / total_job
        self.MAX_COMM_COST = None
        self.MIN_COMM_COST = None
        self.define_max_comm_cost()

    def define_max_comm_cost(self):
        # TODO: by now i am hard coding the max communications cost, but it should be based in the infra-*.json file
        self.MAX_COMM_COST = dict()
        self.MIN_COMM_COST = dict()

        # index is the number of gpus and the value is the worst case max cost
        self.MAX_COMM_COST[1] = self.MIN_COST
        self.MAX_COMM_COST[2] = 40.0
        self.MAX_COMM_COST[3] = 60.0

        self.MIN_COMM_COST[1] = self.MIN_COST
        self.MIN_COMM_COST[2] = 1.0
        self.MIN_COMM_COST[3] = 41.0

    def get_comm_cost(self, curr_glist, all_gpus, curr_partit_com_cost, external_part_com_cost, external_comm=False):
        """
            # Calculate the communication cost for each gpu with all other GPUs.
            # This metric is used for measuring Utility, then it returns the inversion of the cost. This means that lower
              cost will lead to higher satisfaction.
        """
        if external_part_com_cost is None:
            external_comm = False
        cost = 0.0
        # First it calculates the sum of the communications between all possible pairs of gpus from the given list
        gpuids = list()
        for pair in list(itertools.combinations(curr_glist, 2)):
            gpu1, gpu2 = list(pair)
            gpuids.append(gpu1.id)
            gpuids.append(gpu2.id)
            if external_comm:
                cost += external_part_com_cost[gpu2.id][gpu1.id]
            if gpu1.id in curr_partit_com_cost:
                if gpu2.id in curr_partit_com_cost[gpu1.id]:
                    cost += curr_partit_com_cost[gpu1.id][gpu2.id]
            elif gpu2.id in curr_partit_com_cost:
                if gpu1.id in curr_partit_com_cost[gpu2.id]:
                    cost += curr_partit_com_cost[gpu2.id][gpu1.id]

        # Second, if there is other gpus in other partitions, calculate the communication cost of the given gpus with gpus
        # from the other partition
        if external_comm and external_part_com_cost is not None:
            for gpu1 in list(curr_glist):
                for gpu2 in all_gpus:
                    # account only the GPUs from the neighbour partition, that is the one not in glist
                    if gpu2.id not in gpuids:
                        cost += external_part_com_cost[gpu2.id][gpu1.id]

        # if cost <= self.MIN_COMM_COST[len(curr_glist)]:
        #     return self.MIN_COST

        # To make a fair comparison between the utility of jobs allocating one, two or three me remove from the overall
        # cost the minimal cost related to the number of GPUs

        if cost > 0.0:
            cost = cost - self.MIN_COMM_COST[len(curr_glist)]
        if cost == 0.0:
            return self.MIN_COST

        return cost

    def get_gpu_positions(self, glist):
        """If the GPUs are in the same socket, it returns intra, otherwise inter 'socket'"""
        gpu1_socket = glist[0].socket
        socket_list = list()
        place = "intra-socket"
        for gpu in glist:
            socket_list.append(gpu.socket)
            if gpu.socket != gpu1_socket:
                place = "inter-socket"
        return place, set(socket_list)

    def same_socket(self, job, socket_list):
        for gpu_list in job.placement.gpu_per_socket:
            for gpu in gpu_list:
                if gpu['hgpu'].socket in socket_list:
                    return True
        return False

    def get_interference_in_job(self, A, P, glist, profile):
        """
            This method calculate the interfere that the given job will suffer from the already running jobs.
            It returns the mean slowdown of the collocation of the all the pairs of the current job with all running jobs.
            The index is calculated dividing the execution time in solo-mode per collocation-mode. Where solo will be
            always lower than collocation. Therefore, this index will be within the interval [0,1].
            The collocation of jobs in the profile returns the execution time of the first listed job, which represents
            the execution time of the the first listed job in the presence of the second job.
        """
        slowdown = 0.0
        num_gpus = str(len(glist))
        place, socket_list = self.get_gpu_positions(glist)

        # TODO: what to do if the profile does not exist???
        profile_exist = False
        if A.type in profile["collocation"]:
            if str(A.size) in profile["collocation"][A.type]:
                if num_gpus in profile["collocation"][A.type][str(A.size)]["num_gpus"]:
                    profile_exist = True

        if profile_exist:
            solo_time = profile["solo"][A.type][str(A.size)]["num_gpus"][num_gpus][place]
            collocation = profile["collocation"][A.type][str(A.size)]["num_gpus"][num_gpus]
            _, socket_list = self.get_gpu_positions(glist)

            interference = False
            for job in P.running_jobs.values():
                if job.id != A.id:
                    jnum_gpus = str(job.get_num_gpus())
                    if self.same_socket(job, socket_list):
                        if job.type in profile["collocation"]:
                            if str(job.size) in collocation[job.type]:
                                if jnum_gpus in collocation[job.type][str(job.size)]["num_gpus"]:
                                    colloc_time = collocation[job.type][str(job.size)]["num_gpus"][jnum_gpus]
                                    if colloc_time > 0:
                                        slowdown_tmp = solo_time / float(colloc_time)
                                        # If the execution time of the application will be reduce with the collocation
                                        if slowdown_tmp < 1:
                                            slowdown += solo_time / float(colloc_time)
                                            interference = True
                    else:
                        print "profile does not exist", A.type, str(A.size), len(glist), job.type, str(job.size), jnum_gpus

                        # Make the average.
            if interference:
                if len(P.running_jobs.values()) > 0:
                    slowdown /= len(P.running_jobs.values())

        if slowdown == 0.0:
            return self.MIN_COST

        return slowdown

    def get_interference_on_other_jobs(self, A, P, glist, profile):
        """
            This method calculate the interfere that the given job will suffer from the already running jobs.
            It returns the mean slowdown of the collocation of the all the pairs of the current job with all running jobs.
            The index is calculated dividing the execution time in solo-mode per collocation-mode. Where solo will be
            always lower than collocation. Therefore, this index will be within the interval [0,1].
            The collocation of jobs in the profile returns the execution time of the first listed job, which represents
            the execution time of the the first listed job in the presence of the second job.
        """
        slowdown = 0.0
        num_gpus = str(len(glist))
        place, socket_list = self.get_gpu_positions(glist)

        interference = 0
        for job in P.running_jobs.values():
            if job.id != A.id:
                jnum_gpus = str(job.get_num_gpus())

                # TODO: what to do if the profile does not exist???
                profile_exist = False

                if job.type in profile["collocation"]:
                    if str(job.size) in profile["collocation"][job.type]:
                        if num_gpus in profile["collocation"][job.type][str(job.size)]["num_gpus"]:
                            profile_exist = True
    
                if profile_exist:
                    solo_time = profile["solo"][job.type][str(job.size)]["num_gpus"][num_gpus][place]
                    collocation = profile["collocation"][job.type][str(job.size)]["num_gpus"][num_gpus]
                    _, socket_list = self.get_gpu_positions(glist)

                    if self.same_socket(job, socket_list):
                        if A.type in profile["collocation"]:
                            if str(A.size) in collocation[A.type]:
                                if jnum_gpus in collocation[A.type][str(A.size)]["num_gpus"]:
                                    colloc_time = collocation[A.type][str(A.size)]["num_gpus"][jnum_gpus]
                                    if colloc_time > 0:
                                        slowdown_tmp = solo_time / float(colloc_time)
                                        # If the execution time of the application will be reduce with the collocation
                                        if slowdown_tmp < 1:
                                            slowdown += solo_time / float(colloc_time)
                                            interference += 1
 
        if interference > 0:
            if len(P.running_jobs.values()) > 0:
                slowdown /= interference

        if slowdown == 0.0:
            return self.MIN_COST

        return slowdown

    def get_fragmentation(self, P, glist):
        """ Account average of the proportion of free GPUs less the ones that will be allocated to the job
            If the proportion is 1, it means that all GPUs were allocated and fragmentation is 0.
        """
        num_gpus_to_alloc = len(glist)
        frag = 0.0
        for socket in P.sockets:
            current_free_gpus = socket.get_free_gpus()
            after_alloc_free = len(current_free_gpus)

            # remove from the free gpu list the gpus that will be allocated to the job
            for fgpu in current_free_gpus:
                add = True
                for alloc_gpus in glist:
                    if fgpu.id == alloc_gpus.id:
                        add = False
                if add and num_gpus_to_alloc > 0:
                    after_alloc_free -= 1
                    num_gpus_to_alloc -= 1

            frag += after_alloc_free / float(socket.total_gpus)

        frag /= len(P.sockets)

        if frag == 0.0 or frag == 1.0:
            return self.MIN_COST


        return frag

    def normalize_cost(self, metric, cost):
        worst = 1
        if "comm" in metric:
            if len(cost['gpus']) > 1:
                worst = self.MAX_COMM_COST[len(cost['gpus'])]
            else:
                return self.MIN_COST
        norm = cost[metric] / worst

        if norm < self.MIN_COST:
            return self.MIN_COST

        return cost[metric] / worst

    def calculate_utility(self, costs, system=True):
        """
            We normalize the calculated utility with the maximum utility that the current configuration can give
            For the application utility, it does not consider the fragmentation metric, which is a system parameter
            Therefore, this method returns a utility within the interval [0, 1]
        """
        lengh = len(self.policy['weight'])
        if not system:
            lengh -= 1

        cost = 0.0
        for metric in self.policy['weight']:
            norm_cost = self.normalize_cost(metric, costs)
            if not system:
                if 'frag' in metric:
                    continue
                # if we remove a metric, we should equally distribute its weight among the other indexes
                cost += norm_cost ** (self.policy['weight'][metric] + self.policy['weight'][metric]/lengh)
            else:
                value = self.policy['weight'][metric]
                if "interf" in metric:
                    if 'interference_on_other_jobs' in costs:
                        norm_cost += self.normalize_cost('interference_on_other_jobs', costs)
                        norm_cost /= 2

                cost += norm_cost ** value

        if cost == 0:
            return 1

        if not system:
            return (1 / cost) / self.MAX_JOB_UTILITY
        return (1 / cost) / self.MAX_SYS_UTILITY
