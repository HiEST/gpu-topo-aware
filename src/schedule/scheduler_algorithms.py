#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# The second queue is used to add the jobs that could not be placed in the current scenario, e.g. load. This queue
# is defined to have priority against the former queue.
#
# Copyright © 2017 Marcelo Amaral <marcelo.amaral@bsc.es>

import json

from src.schedule.algorithms import fcfs, bf, utilityaware


class Algorithm:
    def __init__(self, config, utility):
        self.algo_name = json.loads(config.get("scheduler", "sched_type"))
        self.config = config
        self.utility = utility

    def execute(self, curr_time, queue1, queue2, cluster_resources, job_profile):
        method = getattr(self, self.algo_name)
        return method(curr_time, queue1, queue2, cluster_resources, job_profile)

    def fcfs(self, curr_time, queue1, queue2, cluster_resources, job_profile):
        return fcfs.fcfs(curr_time, queue1, queue2, cluster_resources, job_profile, self.utility)

    def bf(self, curr_time, queue1, queue2, cluster_resources, job_profile):
        return bf.bf(curr_time, queue1, queue2, cluster_resources, job_profile, self.utility)

    def utilityaware(self, curr_time, queue1, queue2, cluster_resources, job_profile):
        postpone = json.loads(self.config.get("scheduler", "postpone"))
        return utilityaware.utilityaware(curr_time, queue1, queue2, cluster_resources, job_profile,
                                         self.utility, postpone)
