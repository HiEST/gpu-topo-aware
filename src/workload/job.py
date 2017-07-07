#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Contains all job info plus the placement info.
#
# Copyright © 2017 Marcelo Amaral <marcelo.amaral@bsc.es>

import json
import configparser


class Costs:
    def __init__(self):
        self.comm = None
        self.suffered_interf = None
        self.caused_interf = None
        self.frag = None


class Placement:
    def __init__(self):
        self.machine = None
        self.mem_per_socket = []
        self.core_per_socket = []
        self.gpu_per_socket = []
        self.placed = False
        self.start_time = None
        self.end_time = None
        self.job_utility = None
        self.system_utility = None
        self.submitted_time = None
        self.costs = Costs()


class Job:
    def __init__(self, job):
        # Loading the job's resources
        self.id = job['id']
        self.type = job['type']
        self.tasks = job['tasks']
        self.mem = job['mem']
        self.gpus = [x for x in range(job['gpus'])]
        self.size = job['size']  # for different application the size means differently, e.g. for caffe is batch size
        self.color = job['color']  # this parameter is only useful for plotting
        self.minimal_utility = job['minimal_utility']
        self.arrival_time = job['arrival']  # arrival time following a distribution
        self.exec_time = job['time']

        # Creating the GPUs communication matrix
        self.comm_matrix = create_comm_matrix(self.get_num_gpus())
        # Creating the placement information
        self.placement = Placement()

    def get_num_gpus(self):
        return len(self.gpus)

    def get_alloc_gpus(self):
        gpus = list()
        for pairs in self.placement.gpu_per_socket:
            if len(pairs) > 0:
                pairs = sorted(pairs, key=lambda t: t['hgpu'].id, reverse=False)
                for pair in pairs:
                    gpus.append(pair['hgpu'])
        return gpus

    def get_comm_intensity(self):
        comm = 0
        for column in self.comm_matrix:
            for row in column:
                comm += row
        size = len(self.comm_matrix) + len(self.comm_matrix[0])
        return comm / size

    def get_profile(self, job):
        profile = configparser.ConfigParser(delimiters=("="))
        profile.read("../etc/" + str(job['type']) + "-" + str(job['size']) + ".ini")
        return profile

    def get_interference(self, job, coll_jobs):
        profile = self.get_profile(job)
        interf = 0
        for collj in coll_jobs:
            interf += json.loads(profile.get("interference", str(collj['type']) + "-" + str(collj['size'])))
        interf /= len(coll_jobs)
        return interf

    # This method prints the job's information in two different ways. If placement is true, it prints the placement
    # information, otherwise, it only prints information about the job.
    def to_string(self, placement_info=True):
        s = "Id: " + str(self.id)
        s += ", Was placed: " + str(self.placement.placed)
        s += ", Utility: (Job:" + str(self.placement.job_utility)
        s += ", Sys:" + str(self.placement.system_utility)
        s += "), Costs: (Comm:" + str(self.placement.costs.comm) + \
             ", Suffered_Interf:" + str(self.placement.costs.suffered_interf) + \
             ", Caused_Interf:" + str(self.placement.costs.caused_interf) + \
             ", Frag: " + str(self.placement.costs.frag)
        s += "), Type: " + str(self.type)
        s += ", Size: " + str(self.size)
        s += ", Arrival: " + str(self.arrival_time)
        s += ", ExecTime: " + str(self.exec_time)
        if not placement_info:
            s += ", Requested GPUs: " + str(self.get_num_gpus())
            s += ", MainMem: " + str(self.mem)
            s += ", Tasks: " + str(self.tasks)
        else:
            s += ", Machine: " + str(self.placement.machine)
            s += ", Allocated GPUs: "
            for socket, gpus in enumerate(self.placement.gpu_per_socket):
                s += "S" + str(socket) + "["
                for aux, gpu in enumerate(gpus):
                    if aux == len(gpus) - 1:
                        # s += str(gpu.id)
                        s += str(gpu['hgpu'].id)
                    else:
                        # s += str(gpu.id) + ","
                        s += str(gpu['hgpu'].id) + ","
                s += "]"
            s += ", MainMem: " + str(self.placement.mem_per_socket)
            s += ", Tasks: " + str(self.placement.core_per_socket)

        return s


# TODO: Communication matrix it might be defined in the profile; some GPUs might have different comm
def create_comm_matrix(gpus):
    return [[1 for _ in range(gpus)] for _ in range(gpus)]
