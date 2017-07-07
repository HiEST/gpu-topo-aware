#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Keeps the list of resources in the cluster.
#
# Copyright © 2017 Marcelo Amaral <marcelo.amaral@bsc.es>


class GPU:
    def __init__(self, id, socket):
        self.id = str(id)
        # self.type = None
        # self.mem = None
        # self.clock = None
        # topology levels
        self.socket = socket  # Connection traversing PCIe as well as the SMP link between CPU sockets(e.g. QPI)
        # self.pix = None  # Connection traversing PCIe as well as a PCIe Host Bridge (typically the CPU)
        # self.phb = None  # Connection traversing multiple PCIe switches (without traversing the PCIe Host Bridge)
        # self.pxb = None  # Connection traversing a single PCIe switch
        self.nvl = 1  # Connection traversing a bonded set of # NVLinks
        self.allocated = False


def create_gpus(gpu_per_socket, socket_id, index):
    gpus = list()
    for socket in range(gpu_per_socket):
        gpus.append(GPU(index, socket_id))
        index += 1
    return gpus


class Socket:
    def __init__(self, id, name, mem, cores, gpus, gpu_index):
        self.id = id
        self.name = name
        # Total resources
        self.mem = mem
        self.cores = cores
        self.gpus = create_gpus(gpus, id, gpu_index)
        self.total_gpus = len(self.gpus)
        # Allocated resources
        self.allocated_mem = 0
        self.allocated_cores = 0

    def get_free_gpus(self):
        gpus = list()
        for gpu in self.gpus:
            if not gpu.allocated:
                gpus.append(gpu)
        return gpus


def create_sockets(resources):
    sockets = list()
    index = 0
    gpu_index = 0
    for socket in range(len(resources["mem_per_socket"])):
        name = resources["sockets"][socket]
        mem = resources["mem_per_socket"][socket]
        cores = resources["core_per_socket"][socket]
        gpus = resources["gpu_per_socket"][socket]
        sockets.append(Socket(index, name, mem, cores, gpus, gpu_index))
        index += 1
        gpu_index = gpus
    return sockets


class Machine:
    def __init__(self, resources, machine_type, mid):
        # Loading the physical resources
        self.sockets = create_sockets(resources)
        self.socket_distance = resources["socket_distance"]
        self.gpu_distance = resources["gpu_distance"]
        self.running_jobs = dict()
        self.finished_jobs = dict()
        self.id = mid
        self.machine_type = machine_type

    def get_all_gpus(self):
        l = list()
        for socket in self.sockets:
            for gpu in socket.gpus:
                l.append(gpu)
        return l

    def get_free_gpus(self):
        l = list()
        for socket in self.sockets:
            for gpu in socket.gpus:
                if not gpu.allocated:
                    l.append(gpu)
        return l

    # Total physical resources --------------------------------
    def get_total_mem(self):
        mem = 0
        for socket in self.sockets:
            mem += socket.mem
        return mem

    def get_total_cores(self):
        cores = 0
        for socket in self.sockets:
            cores += socket.cores
        return cores

    def get_total_num_gpus(self):
        gpus = 0
        for socket in self.sockets:
            gpus += len(socket.gpus)
        return gpus

    def get_total_free_gpus_in_socket(self, socket):
        gpus = 0
        for gpu in self.sockets[socket].gpus:
            if not gpu.allocated:
                gpus += 1
        return gpus

    # ---------------------------------------------------------

    # total allocated resources  ------------------------------
    def get_total_alloc_mem(self):
        mem = 0
        for socket in self.sockets:
            mem += socket.allocated_mem
        return mem

    def get_total_alloc_cores(self):
        cores = 0
        for socket in self.sockets:
            cores += socket.allocated_cores
        return cores

    def get_total_alloc_gpus(self):
        gpus = 0
        for socket in self.sockets:
            for gpu in socket.gpus:
                if gpu.allocated:
                    gpus += 1
        return gpus

    # ---------------------------------------------------------

    # total allocatable resources -----------------------------
    def get_total_free_mem(self):
        return self.get_total_mem() - self.get_total_alloc_mem()

    def get_total_free_cores(self):
        return self.get_total_cores() - self.get_total_alloc_cores()

    def get_total_free_gpus(self):
        return self.get_total_num_gpus() - self.get_total_alloc_gpus()

    # ---------------------------------------------------------

    # max allocatable resources per socket --------------------
    def get_free_mem_per_socket(self, sid):
        return self.sockets[sid].mem - self.sockets[sid].allocated_mem

    def get_free_core_per_socket(self, sid):
        return self.sockets[sid].cores - self.sockets[sid].allocated_cores

    def get_free_gpu_per_socket(self, sid):
        total = 0
        alloc = 0
        for gpu in self.sockets[sid].gpus:
            total += 1
            if gpu.allocated:
                alloc += 1
        return total - alloc

    # ---------------------------------------------------------

    # Allocate or deallocate resources from the machine -------
    def alloc_mem_in_socket(self, sid, mem, alloc=True):
        if alloc:
            self.sockets[sid].mem += mem
        else:
            self.sockets[sid].mem -= mem

    def alloc_core_in_socket(self, sid, cores, alloc=True):
        if alloc:
            self.sockets[sid].cores += cores
        else:
            self.sockets[sid].cores -= cores

    def alloc_gpu_in_socket(self, sid, job_gpus, alloc=True):
        for job_gpu in job_gpus:
            gpuid = job_gpu['hgpu'].id
            for gpu in self.sockets[sid].gpus:
                if gpu.id == gpuid:
                    if alloc:
                        gpu.allocated = True
                    else:
                        gpu.allocated = False
    # ---------------------------------------------------------

    # Allocating resources using the full job information -----
    def alloc_resources(self, job):
        for sid in range(len(self.sockets)):
            self.alloc_mem_in_socket(sid, job.placement.mem_per_socket[sid], alloc=True)
            self.alloc_core_in_socket(sid, job.placement.core_per_socket[sid], alloc=True)
            self.alloc_gpu_in_socket(sid, job.placement.gpu_per_socket[sid], alloc=True)

    def free_resources(self, job):
        for sid in range(len(self.sockets)):
            self.alloc_mem_in_socket(sid, job.placement.mem_per_socket[sid], alloc=False)
            self.alloc_core_in_socket(sid, job.placement.core_per_socket[sid], alloc=False)
            self.alloc_gpu_in_socket(sid, job.placement.gpu_per_socket[sid], alloc=False)

    # ---------------------------------------------------------

    # Graph: return the communication matrix of the GPUs ------
    # TODO: we should create the gpus distance matrix based on nvidia-msi and numactl output
    def get_comm_matrix(self):
        return self.gpu_distance

    # TODO: this function should consider all applications already allocated in this machine giving a function
    # TODO: by now, it is not returning the right values...
    def get_interference_matrix(self):
        return

    def get_fragmentation(self):
        frag = 0.0
        free_gpus = 0
        total_gpus = 0
        for socket in self.sockets:
            free_gpus += len(socket.get_free_gpus())
            total_gpus += socket.total_gpus
            frag += len(socket.get_free_gpus()) / float(socket.total_gpus)

        frag /= len(self.sockets)

        if frag == 1.0:
            frag = 0.0

        return {"free_gpus": free_gpus, "total_gpus": total_gpus, "frag": frag, "mid": self.id}
    # ---------------------------------------------------------

    def to_string(self):
        string = ""
        for socket in self.sockets:
            string += " Socket: " + str(socket.id)
            string += ", gpus: "
            for gpu in socket.gpus:
                if gpu.allocated:
                    string += str(gpu.id) + "/alloc, "
                else:
                    string += str(gpu.id) + "/free, "
        return string