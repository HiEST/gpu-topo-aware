#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# The second queue is used to add the jobs that could not be placed in the current scenario, e.g. load. This queue
# is defined to have priority against the former queue.
#
# Copyright © 2017 Marcelo Amaral <marcelo.amaral@bsc.es>

import os
import json
import time
import random
import collections
from collections import defaultdict

from src.schedule import scheduler_algorithms as sched_algo
from src.workload.job import Job

from src.system.enforcement import executor


class Scheduler:
    def __init__(self, config, cluster_resources, utility, job_profile, output_folder, logger, sim_mode,
                 workload_manifest):
        random.seed(1234)
        self.output_folder = output_folder
        self.queue1 = collections.deque()
        self.queue2 = collections.deque()
        self.config = config
        self.interval = json.loads(self.config.get("scheduler", "interval"))
        self.sched_algo = sched_algo.Algorithm(config, utility)
        self.cluster_resources = cluster_resources
        self.sim_mode = sim_mode
        # TODO: The scheduler should keeps the historical information of all jobs profile
        self.profile = job_profile
        self.stats = dict()
        self.job_executors = defaultdict(dict)
        self.workload_manifest = workload_manifest
        self.logger = logger

    def add_job(self):
        job = yield
        job = Job(job)
        job.exec_time = self.profile["solo"][job.type][job.size]["num_gpus"][len(job.gpus)]["intra-socket"]
        self.queue1.append(job)

    def add_job_from_list(self):
        while True:
            curr_time = yield
            job_list = yield
            for j_info in job_list:
                job = Job(j_info)
                job.exec_time = self.profile["solo"][job.type][job.size]["num_gpus"][str(len(job.gpus))]["intra-socket"]
                job.placement.submitted_time = curr_time
                self.queue1.append(job)

    # TODO: these following two procedure are duplicated in the class Utility
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

    def get_job_exec_time(self, job):
        glist = list()
        for socket in job.placement.gpu_per_socket:
            for gpu in socket:
                glist.append(gpu['hgpu'])

        place, socket_list = self.get_gpu_positions(glist)

        solo_time = self.profile["solo"][job.type][job.size]["num_gpus"][str(len(glist))][place]
        collocation = self.profile["collocation"][job.type][job.size]["num_gpus"][str(len(glist))]
        colloc_time = 0

        for job2 in self.cluster_resources.machines[job.placement.machine].running_jobs.values():
            if job.id != job2.id:
                if self.same_socket(job2, socket_list):
                    j2num_gpus = str(job2.get_num_gpus())
                    if job2.type in collocation:
                        if job2.size in collocation[job2.type]:
                            if j2num_gpus in collocation[job2.type][job2.size]["num_gpus"]:
                                colloc_time2 = collocation[job2.type][job2.size]["num_gpus"][j2num_gpus]
                                print "Collocation ", job.id, job2.id
                                if colloc_time2 > colloc_time:
                                    colloc_time = colloc_time2

        if colloc_time > solo_time:
            if colloc_time >= job.exec_time:
                job.exec_time = colloc_time
                print "#############: Job ", job.id, " was delayed from: ", solo_time, " to ", colloc_time
                return colloc_time
        if solo_time > job.exec_time:
            job.exec_time = solo_time
        return job.exec_time

    def update_job_state(self, job, curr_time):
        job_exec_time = None
        if self.sim_mode:
            job_exec_time = self.get_job_exec_time(job)
            self.logger.info(
                "## Job " + str(job.id) + " has started in: " + str(job.placement.start_time) +
                ", need to execute: " + str(job_exec_time) + " and executed: " +
                str(curr_time - job.placement.start_time) + ". Current time: " + str(curr_time))

            if job_exec_time <= (curr_time - job.placement.start_time):
                cluster_resources = self.cluster_resources.machines
                job.placement.end_time = curr_time
                machine = cluster_resources[job.placement.machine]
                machine.free_resources(job)
                machine.finished_jobs[job.id] = job
                #TODO: call statistics here
                del machine.running_jobs[job.id]
                self.logger.info("## Job " + str(job.id) + " has finished in: " + str(curr_time))
        else:
            for jid, e in self.job_executors.iteritems():
                if jid == job.id:
                    job_exec_time = e['executor'].get_time()
                    self.logger.info(
                        "## Job " + str(job.id) + " has started in: " + str(job.placement.start_time) +
                        " and executed: " + str(job_exec_time) + ". Current time: " + str(curr_time))
                    if e['executor'].has_finished():  # if job has finished
                        cluster_resources = self.cluster_resources.machines
                        job.placement.end_time = curr_time
                        machine = cluster_resources[job.placement.machine]
                        machine.free_resources(job)
                        machine.finished_jobs[job.id] = job
                        # TODO: call statistics here
                        del machine.running_jobs[job.id]
                        self.logger.info("## Job " + str(job.id) + " has finished in: " + str(curr_time))

        return job_exec_time

    def update_cluster_state(self, curr_time):
        """Verify if jobs have finished or if the load has changed"""

        for id, machine in self.cluster_resources.machines.items():
            jobs = machine.running_jobs.keys()
            for jid in jobs:
                job = self.cluster_resources.machines[id].running_jobs[jid]
                exec_time = self.update_job_state(job, curr_time)

                if jid in self.cluster_resources.machines[id].running_jobs:  # It might have been deleted already
                    self.cluster_resources.machines[id].running_jobs[jid].exec_time = exec_time
                # job.placement.exec_time = self.update_job_state(job, curr_time)

    def enforce_placement(self, job):
        machine = job.placement.machine
        self.cluster_resources.machines[machine].alloc_resources(job)
        if not self.sim_mode:
            self.execute_job(job)

    def execute_job(self, job):
        """This function creates a thread that will execute the job and track its ending"""
        cwd = os.getcwd()
        script = os.path.join(cwd, "data/workload-manifest/scripts_to_run/" + self.workload_manifest)
        out_directory = self.output_folder + "logs"

        # create command to execute
        cmd = list()
        cmd.append(script)
        # job_id
        cmd.append(str(job.id))  # Job ID
        # net
        cmd.append(str(job.type))  # Application name/type
        # size
        cmd.append(str(job.size))  # Application size

        glist = None

        for socket in job.placement.gpu_per_socket:
            for gpu_info in socket:
                gpu = gpu_info['hgpu']
                if glist is None:
                    glist = str(gpu.id)
                else:
                    glist += "," + str(gpu.id)

        # gpus
        gpus = job.get_alloc_gpus()  # Allocated gpus
        num_gpus = len(gpus)
        gpus_str = ""
        gpus_name_str = ""
        for i in range(num_gpus):
            gpus_str += str(gpus[i].id)
            gpus_name_str += str(gpus[i].id)
            if i < num_gpus - 1:
                gpus_str += ","
                gpus_name_str += "-"

        # numgpus
        cmd.append(str(num_gpus))
        cmd.append(gpus_str)
        # gpus_name
        cmd.append(gpus_name_str)
        # dir
        cmd.append(out_directory)  # Directory for the output
        # numactl
        numactl = ""
        if (num_gpus == 1) or ("0,1" in gpus_str):
            numactl = "numactl -N 0 -m 0"  # TODO: it should not be hard coded

        cmd.append(numactl)  # TODO: it should not be hard coded

        e = executor.create_job(cmd)
        self.job_executors[job.id]['executor'] = e
        self.job_executors[job.id]['job'] = job
        # self.cluster_resources.machines[job.placement.machine].executor[job.id]['executor'] = e

        self.logger.info("####### CMD: " + str(cmd))

    def run(self):
        while True:
            curr_time = yield

            if len(self.queue1) > 0 or len(self.queue2) > 0:
                self.logger.info("")
                self.logger.info("---- Scheduler Iteration: " + str(curr_time) + " ----")
                time_before = time.time()
                #for mid, machine in self.cluster_resources.machines.iteritems():
                #    self.logger.info("Resources: Machine ID: " + str(mid) + machine.to_string())
                decision = self.sched_algo.execute(curr_time, self.queue1, self.queue2, self.cluster_resources, self.profile)
                elapsed_time = str(time.time() - time_before)
                self.stats[curr_time] = dict()
                self.stats[curr_time]["num_jobs"] = len(self.queue1) + len(self.queue2)
                self.stats[curr_time]["sched_time"] = elapsed_time
                #self.logger.info("Scheduler algorithm num jobs to be sched= " + str(len(self.queue1) + len(self.queue2)) + " execution time= " +
                #             str(elapsed_time))

                for job in decision:
                    if not job.placement.placed:
                        self.logger.info("Job " + job.to_string(placement_info=False))
                        for qjob in self.queue1:
                            if job.id == qjob.id:
                                self.queue1.remove(qjob)
                        self.queue2.append(job)
                    else:
                        self.logger.info("Job " + job.to_string())
                        machine = self.cluster_resources.machines[job.placement.machine]
                        machine.running_jobs[job.id] = job
                        job.placement.start_time = curr_time
                        self.enforce_placement(job)
                        for qjob in self.queue1:
                            if job.id == qjob.id:
                                self.queue1.remove(qjob)
                        for qjob in self.queue2:
                            if job.id == qjob.id:
                                self.queue2.remove(qjob)
            else:
                msg = " queue1:" + str(len(self.queue1)) + " queue2:" + str(len(self.queue2))
                self.logger.info("There is no job to be scheduled " + msg)
            self.update_cluster_state(curr_time)
