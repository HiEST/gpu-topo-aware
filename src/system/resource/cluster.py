#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Keeps the list of resources in the cluster.
#
# Copyright © 2017 Marcelo Amaral <marcelo.amaral@bsc.es>

import os
import json

import machine


class Cluster:
    def __init__(self, config, num_machines):
        n, resources = self.read_config(config)
        if num_machines <= 0:
            num_machines = n
        self.resources = resources
        self.machines = self.set_machines(self.resources, num_machines)
        self.profiles = self.set_profile(config)

    def set_profile(self, config):
        """The profile describes the execution time of collocated applications. Because we have a simple topology
        with only four GPUs and two sockets, the collocation is always meaning applications in both sockets. Such as:
        application1 in 0-2 and application2 in 1-3. They are sharing the same inter-socket communication bus."""

        file_name = json.loads(config.get("workload", "profile"))
        cwd = os.getcwd()
        path = os.path.join(cwd, "data/profiles/" + file_name + ".json")
        with open(path, "r") as f:
            data = f.read()
        return json.loads(data)

    def set_machines(self, config, num_machines):
        machines = dict()

        for id in range(num_machines):
            for type, mr in config["machines"].iteritems():
                machines[id] = machine.Machine(mr, type, id)

        print len(machines)

        return machines

    def read_config(self, config):
        # TODO: the num_machines should also indicate the machine type
        num_machines = json.loads(config.get("system", "num_machines"))
        infra_file = json.loads(config.get("system", "infrastructure"))
        cwd = os.getcwd()
        path = os.path.join(cwd, "etc/" + infra_file + ".json")
        with open(path, "r") as f:
            data = f.read()
            cluster_physical_resources = json.loads(data)
        return num_machines, cluster_physical_resources

    def get_num_free_gpus(self):
        gpus = 0
        for id, machine in self.machines.iteritems():
             gpus += len(machine.get_free_gpus())
        return gpus

    def get_max_free_gpus_per_machine(self):
        gpus = 0
        for id, machine in self.machines.iteritems():
            if len(machine.get_free_gpus()) > gpus:
                gpus = len(machine.get_free_gpus())
        return gpus

    def get_free_gpus(self):
        gpus = dict()
        for id, machine in self.machines.iteritems():
            machine_gpus = machine.get_free_gpus()
            if len(machine_gpus) > 0:
                if machine.id not in gpus:
                    gpus[machine.id] = dict()
                gpus[machine.id] = machine_gpus
        return gpus