#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This is the system framework, which can work in real-time or simulator mode.
#
# Copyright © 2017 Marcelo Amaral <marcelo.amaral@bsc.es>

import os
import copy
import json
import time
from collections import OrderedDict

from src.schedule.algorithms.utils import utility
from src.simulator import simulator
from src.system.resource import resources

from src.schedule import scheduler


class System:
    def __init__(self, sys_config, sched_config, folder, logger, start_time, num_machines=0):
        self.sys_config = sys_config
        self.sched_config = sched_config
        self.output_folder = folder
        self.sim_mode = self.sys_config.getboolean("simulator", "enabled")
        self.sim = simulator.Simulator(self.sys_config)
        self.step = self.sim.step()
        self.system_start_time = start_time
        self.resources = resources.create(self.sys_config, num_machines)
        self.utility = utility.Utility(self.sched_config)
        self.profile = self.load_profile()
        self.logger = logger
        self.scheduler = scheduler.Scheduler(self.sched_config, self.resources.cluster, self.utility, self.profile,
                                             self.output_folder, self.logger,
                                             self.sim_mode, str(json.loads(self.sys_config.get("workload", "manifest"))))
        self.arrivals = dict()  # job IDs indexed by arrival time
        # Statistics
        self.system_stats = []
        self.placement_stats = dict()
        self.sched_stats = dict()

    def load_profile(self):
        cwd = os.getcwd()
        path = os.path.join(cwd, "data/profiles/" + json.loads(self.sys_config.get("workload", "profile")) + ".json")
        return json.load(open(path, "r"))

    def get_elapsed_time(self):
        if self.sim_mode:
            return self.sim.curr_time
        else:
            return time.time() - self.system_start_time

    def get_jobs(self):
        jobs = None
        if len(self.arrivals) > 0:
            arrival = sorted(self.arrivals.iteritems(), key=lambda t: t[0], reverse=False)
            time = arrival[0][0]
            if time <= self.get_elapsed_time():
                jobs = copy.deepcopy(self.arrivals[time])
                del self.arrivals[time]

        return jobs

    def get_not_stop(self):
        """Return False if the system must stop"""
        self.next_time()
        t = True
        if self.sim_mode:
            t = (self.get_elapsed_time() <= self.sim.length)

        num_running = 0
        for machine in self.resources.cluster.machines.values():
            num_running += len(machine.running_jobs)

        l = (num_running > 0) or (len(self.scheduler.queue1) > 0) or \
            (len(self.scheduler.queue2) > 0)

        m = False
        if len(self.arrivals) > 0:
            m = True
        msg = "DEBUG: The system will stop because of: time=" + str(t)
        msg += " running or queued jobs=" + str(l)
        msg += " jobs will arrive: " + str(m)
        self.logger.debug(msg)
        stop = (t and l) or (m and t)
        return stop
        # else:
        #     return True

    def wait(self, t):
        """The waiting time reduce the computation intensity of the scheduler and only matter if it is not
        the simulator mode"""
        if not self.sim_mode:
            return time.sleep(t)

    def next_time(self):
        """This method is the core of the simulator mode. It might return the simulated time or the current time"""
        if self.sim_mode:
            """
            next_event_time = None
            for machine in self.resources.cluster.machines.values():
                jobs = sorted(machine.running_jobs.iteritems(), key=lambda t: t[1].exec_time, reverse=False)
                if len(jobs) > 0:
                    job = jobs[0][1]
                    tmp = job.exec_time - (self.get_elapsed_time() - job.placement.start_time)
                    if next_event_time is not None:
                        if tmp <= next_event_time:  # Update the time of the closest event
                            next_event_time = self.get_elapsed_time() + tmp
                    else:
                        next_event_time = self.get_elapsed_time() + tmp

            if next_event_time is not None:
                self.sim.curr_time = next_event_time
            else:
            """
            next(self.step)

        return self.get_elapsed_time()

    def create_job_stats(self, curr_time, job, machine):
        glist = []
        placement_stats = dict()
        placement_stats["id"] = job.id
        placement_stats["curr_time"] = curr_time
        placement_stats["start_time"] = job.placement.start_time
        placement_stats["submitted_time"] = job.placement.submitted_time
        placement_stats["end_time"] = job.placement.end_time
        placement_stats['machine'] = job.placement.machine
        placement_stats["color"] = job.color
        placement_stats['gpus'] = list()
        for socket in job.placement.gpu_per_socket:
            for gpu in socket:
                glist.append(gpu['hgpu'])
                placement_stats['gpus'].append(gpu['hgpu'].id)
        placement_stats['communication'] = self.utility.get_comm_cost(glist, glist, machine.gpu_distance,
                                                                      machine.gpu_distance)
        placement_stats["interference"] = self.utility.get_interference_in_job(job, machine, glist, self.profile)
        placement_stats["fragmentation"] = self.utility.get_fragmentation(machine, glist)
        placement_stats["job_utility"] = self.utility.calculate_utility(placement_stats, system=False)
        placement_stats["sys_utility"] = self.utility.calculate_utility(placement_stats)
        return placement_stats

    def save_stats(self, curr_time, sched_stats, cluster_resources):
        # Scheduler
        save = True  # Only save stats when a job has finished

        system = dict()
        system['machines'] = dict()
        system["free_gpus"] = 0
        system["total_gpus"] = 0
        system["frag"] = 0
        system["curr_time"] = curr_time
        num_machines = 0
        for mid, machine in cluster_resources.machines.items():
            if mid not in system['machines']:
                system['machines'][mid] = dict()

            '''Calculate System Fragmentation'''
            num_machines += 1
            s = machine.get_fragmentation()

            stat = system['machines'][mid]
            stat["free_gpus"] = s["free_gpus"]
            stat["total_gpus"] = s["total_gpus"]
            stat["frag"] = s["frag"]
            stat["curr_time"] = curr_time

            system["free_gpus"] += s["free_gpus"]
            system["total_gpus"] += s["total_gpus"]
            system["frag"] += s["frag"]


            #'''Job Costs and Utility'''
            for _, job in machine.running_jobs.iteritems():
               placement_stats = self.create_job_stats(curr_time, job, machine)
               if curr_time not in self.placement_stats:
                   self.placement_stats[curr_time] = dict()
               self.placement_stats[curr_time][job.id] = placement_stats

            '''Job Execution time'''
            """This part is not very efficient, because it searches in all time entries"""
            num_jobs = len(machine.finished_jobs)
            while num_jobs > 0:
                save = True
                job = machine.finished_jobs.popitem()[1]
                num_jobs -= 1

                # # ------------ comment this bloc for a large simulation to reduce the collected info
                placement_stats = self.create_job_stats(curr_time, job, machine)
                if curr_time not in self.placement_stats:
                    self.placement_stats[curr_time] = dict()
                self.placement_stats[curr_time][job.id] = placement_stats
                # # ------------

                for time in self.placement_stats:
                    if job.id in self.placement_stats[time]:
                        stats = self.placement_stats[time][job.id]
                        stats["end_time"] = job.placement.end_time
                        stats["exec_time"] = stats["end_time"] - stats["start_time"]
                    elif job.placement.start_time <= time:  # The statistics was not collected before
                        stats = self.create_job_stats(time, job, machine)
                        stats["end_time"] = job.placement.end_time
                        stats["exec_time"] = stats["end_time"] - stats["start_time"]
                        if curr_time not in self.placement_stats:
                            self.placement_stats[curr_time] = dict()
                        self.placement_stats[curr_time][job.id] = stats

                # # ------------ comment this bloc for a large simulation to reduce the collected info
                placement_stats = dict()
                placement_stats["curr_time"] = curr_time
                placement_stats["start"] = job.placement.start_time
                placement_stats["end"] = job.placement.end_time
                placement_stats["exec_time"] = placement_stats["end"] - placement_stats["start"]
                # # ------------

        if save:
            system["frag"] /= num_machines
            '''Scheduling time'''
            if curr_time in sched_stats.keys():
                self.sched_stats[curr_time] = sched_stats[curr_time]
            self.system_stats.append(system)

    def start(self, jobs):
        # The monitor is not used for simulator. It is responsible to collect the load of real machines
        # if self.monitor is not None:
        for jid, job in jobs.iteritems():
            if self.sim_mode:
                # In simulator mode the running time is different from real time.
                arrival_time = self.get_elapsed_time() + float(self.sim.to_sim_time(float(job["arrival"])))
            else:
                arrival_time = self.get_elapsed_time() + float(job["arrival"])

            if arrival_time not in self.arrivals:
                self.arrivals[arrival_time] = list()
            self.arrivals[arrival_time].append(job)
        self.arrivals = OrderedDict(self.arrivals)

        # Initialize the scheduler and run
        sched_queue = self.scheduler.add_job_from_list()

        sched = self.scheduler.run()

        sched_queue.send(None)
        sched.send(None)
        while self.get_not_stop():
            """The following steps are implemented sequentially to be possible to enable the simulator mode"""
            sched_jobs = self.get_jobs()
            curr_time = self.get_elapsed_time()
            if sched_jobs is not None:
                if len(sched_jobs) > 0:  # stop if there is no more jobs to schedule
                    sched_queue.send(curr_time)
                    sched_queue.send(sched_jobs)

            sched.send(curr_time)

            self.wait(self.scheduler.interval)  # scheduler iteration interval
            self.save_stats(self.get_elapsed_time(), self.scheduler.stats, self.scheduler.cluster_resources)
